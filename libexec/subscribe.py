
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

class VirtualHost:
    def __init__(self, vhost, server, port):
        print("connecting to vhost %s on %s:%d" % (vhost,server,port))
        self.vhost = vhost
        self.connection = Connection(host=server,
                                     port=port,
                                     virtual_host=self.vhost,
                                     mechanism=X509Mechanism(),
                                     ssl_options={"keyfile":os.path.join(IPF_HOME,"etc","key.pem"),
                                                  "certfile":os.path.join(IPF_HOME,"etc","cert.pem"),
                                                  "cert_reqs":ssl.CERT_REQUIRED,
                                                  "ca_certs":os.path.join(IPF_HOME,"etc","ca_certs.pem")},
                                     heartbeat=60)
        self.channel = self.connection.channel()
        self.queue = self.channel.queueDeclare()

    def subscribe(self, exchange, filter):
        print("subscribing to exchange %s in vhost %s for %s" % (exchange,self.vhost,filter))
        queue = self.channel.queueDeclare()
        self.channel.queueBind(queue,exchange,filter)
        consumer_tag = self.channel.basicConsume(self.incoming,queue)
        print("  subscribed to exchange %s in vhost %s for %s" % (exchange,self.vhost,filter))

    def close(self):
        self.connection.close()

    def incoming(self, consumer_tag, routing_key, exchange, content):
        print("|-----------------------------  message  ------------------------------")
        print("|      key: %s" % routing_key)
        print("|    vhost: %s" % self.vhost)
        print("| exchange: %s" % exchange)
        print("|  content:")
        print("%s" % content)

#######################################################################################################################

if __name__ == "__main__":
    usage = "Usage: %prog [options] [<vhost>/<exchange>/<message filter>]+"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-s","--server",default="localhost",dest="server",
                      help="the server running the messaging service")
    parser.add_option("-p","--port",type="int",default=5671,dest="port",
                      help="the port the messaging service is listening to")
    parser.add_option("-v","--vhost",dest="vhost",
                      help="the virtual host in the messaging service to connect to")
    parser.add_option("-e","--exchange",action="append",dest="exchanges",
                      help="an exchange in the virtual host to listen to")
    parser.add_option("-f","--filter",default="#",dest="filter",
                      help="the message filter describing what routing keys are of interest")
    (options, args) = parser.parse_args()

    vhosts = {}
    if options.vhost is not None:
        print("creating vhost from switches...")
        vhosts[options.vhost] = VirtualHost(options.vhost,options.server,options.port)
        if options.exchanges is None or len(options.exchanges) == 0:
            print("vhost specified, but no exchanges specified")
            sys.exit(1)
        else:
            for exchange in options.exchanges:
                vhosts[options.vhost].subscribe(exchange,options.filter)
    else:
        if options.exchanges is not None and len(options.exchanges) > 0:
            print("exchange(s) specified, but no vhost specified")
            sys.exit(1)

    for subscription in args:
        (vhost,exchange,filter) = subscription.split("/")
        if vhost not in vhosts:
            vhosts[vhost] = VirtualHost(vhost,options.server,options.port)
        vhosts[vhost].subscribe(exchange,filter)

    if len(vhosts) == 0:
        print("no subscriptions specified")
        sys.exit(1)

    print("press ctrl-C to exit")
    while keep_running:
        time.sleep(1)
    print("shutting down")

    for vhost in vhosts:
        vhost.close()

#######################################################################################################################
