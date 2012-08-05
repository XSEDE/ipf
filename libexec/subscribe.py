
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
###############################################################################

import logging
import logging.config
import optparse
import os
import signal
import ssl
import sys
import time

from mtk.amqp_0_9_1 import *

from ipf.home import IPF_HOME

logging.config.fileConfig(os.path.join(IPF_HOME,"etc","logging.conf"))

#######################################################################################################################

keep_running = True

def sigHandler(signal, frame):
    global keep_running
    keep_running = False

signal.signal(signal.SIGINT, sigHandler)

#######################################################################################################################

def incoming(consumer_tag, routing_key, exchange, content):
    print("|-----------------------------  message  ------------------------------")
    print("|      key: %s" % routing_key)
    print("| exchange: %s" % exchange)
    print("|  content:")
    print("%s" % content)

#######################################################################################################################

if __name__ == "__main__":
    try:
        filter = sys.argv[1]
        print("receiving glue2 messages about %s" % filter)
    except IndexError:
        filter = "#"
        print("receiving all glue2 messages")

    conn = Connection(host="inca.futuregrid.org",
                      port=5671,
                      virtual_host="monitoring",
                      mechanism=X509Mechanism(),
                      ssl_options={"keyfile":os.path.join(IPF_HOME,"etc","key.pem"),
                                   "certfile":os.path.join(IPF_HOME,"etc","cert.pem"),
                                   "cert_reqs":ssl.CERT_REQUIRED,
                                   "ca_certs":os.path.join(IPF_HOME,"etc","ca_certs.pem")})
    channel = Channel(conn)

    queue = channel.queueDeclare()

    channel.queueBind(queue,"glue2.systems",filter)
    channel.queueBind(queue,"glue2.activities",filter)
    channel.queueBind(queue,"glue2.activity_updates",filter)
    consumer_tag = channel.basicConsume(incoming,queue)

    print("press ctrl-C to exit")
    while keep_running:
        time.sleep(1)
    print("shutting down")

    conn.close()

#######################################################################################################################
