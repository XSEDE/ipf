
###############################################################################
#   Copyright 2011 The University of Texas at Austin                          #
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
import os
import random
import shutil
from ssl import CERT_REQUIRED
import time
import ConfigParser

# pika requires at least Python 2.4 (for @property). A higher version may be needed - 2.6 or better seems ok.

from pika.adapters import SelectConnection
from pika.adapters import BlockingConnection
from pika.connection import ConnectionParameters
from pika.credentials import *
import pika.exceptions
from pika import BasicProperties

from ipf.agent import *

logger = logging.getLogger("AmqpPublishingAgent")

##############################################################################################################

class AmqpPublishingAgent(Agent):

    def __init__(self, args={}):
        Agent.__init__(self,args)
        self.brokers = []
        self.vhost = None
        self.exchange = None
        self.routing_key = None
        self.connection = None
        self.channel = None
        self.error_msg = None

    def run(self, docs_in=[]):
        self._configureBrokers()

        try:
            self.vhost = self.config.get("amqp","vhost")
        except ConfigParser.Error:
            logger.error("amqp.vhost not specified")
            raise AgentError("amqp.vhost not specified")

        try:
            self.exchange = self.config.get("amqp","exchange")
        except ConfigParser.Error:
            logger.error("amqp.exchange not specified")
            raise AgentError("amqp.exchange not specified")

        try:
            self.routing_key = self.config.get("amqp","routing_key")
        except ConfigParser.Error:
            # this is fine - the id in each document will be used
            pass

        self.docs_in = docs_in

        self._connect()
        if self.connection != None:
            self.connection.ioloop.start()

        if self.error_msg != None:
            raise AgentError(self.error_msg)
        return None


    def _configureBrokers(self):
        try:
            brokers_str = self.config.get("amqp","broker")
        except ConfigParser.Error:
            brokers_str = "info1.dyn.teragrid.org:5671,info2.dyn.teragrid.org:5672"

        self.brokers = []
        for hostport in brokers_str.split():
            toks = hostport.split(":")
            self.brokers.append([toks[0],int(toks[1])])
        #random.shuffle(self.brokers)

    def _connect(self):
        if len(self.brokers) == 0:
            self.error_msg = "failed to connect to any of the specified amqp brokers"
            self.connection.ioloop.stop()
            self.connection = None
            return
        (host,port) = self.brokers.pop()
        creds = ExternalCredentials()

        parameters = ConnectionParameters(host, port, self.vhost, creds, ssl=True, ssl_options=self._getSslOptions())
        try:
            self.connection = SelectConnection(parameters,self.on_connected)
        except pika.exceptions.AMQPConnectionError, e:
            raise AgentError(str(e))

    def _getSslOptions(self):
        cacerts_filename = os.path.join(home_dir,"etc","cacerts.pem")
        self._generateCaCertsFile(cacerts_filename)

        try:
            key_file = self.config.get("amqp","key")
        except ConfigParser.Error:
            key_file = "/etc/grid-security/hostkey.pem"
        try:
            cert_file = self.config.get("amqp","certificate")
        except ConfigParser.Error:
            try:
                cert_file = self.config.get("globus","host_certificate")
            except ConfigParser.Error:
                cert_file = "/etc/grid-security/hostcert.pem"

        return {"keyfile": key_file,
                "certfile": cert_file,
                "cert_reqs": CERT_REQUIRED,
                "ca_certs": cacerts_filename}
        
    def _generateCaCertsFile(self, cacerts_filename):
        if os.path.exists(cacerts_filename):
            if os.path.getmtime(cacerts_filename) > time.time() - 7*24*60*60:
                return

        logger.info("generating ca certificates file")
        try:
            cadir = self.config.get("amqp","ca_certificates_directory")
        except ConfigParser.Error:
            try:
                cadir = self.config.get("globus","ca_certificates_directory")
            except ConfigParser.Error:
                cadir = "/etc/grid-security/certificates"
        listing = os.listdir(cadir)
        listing.sort()
        file = open(cacerts_filename,"w")
        for file_name in listing:
            if file_name.endswith(".0"):
                shutil.copyfileobj(open(os.path.join(cadir,file_name),"r"), file)
        file.close()

    def on_connected(self, conn):
        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, ch):
        self.channel = ch
        self.channel.add_on_close_callback(self.on_close)

        for doc in self.docs_in:
            if self.routing_key != None:
                routing_key = self.routing_key
            else:
                routing_key = doc.id
            logger.info("  publishing "+routing_key+" to exchange "+self.exchange)
            self.channel.basic_publish(self.exchange,routing_key,doc.body)

        # wait a little bit for any errors
        self.connection.add_timeout(2,self.on_timeout)

    def on_timeout(self):
        self.connection.close()

    def on_close(self, reply_code, reply_text):
        #print("session closed ("+str(reply_code)+"): "+reply_text)
        if reply_code != 200:
            logger.error(str(reply_code)+": "+reply_text)
            self.error_msg = reply_text
