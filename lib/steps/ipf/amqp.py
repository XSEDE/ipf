#!/usr/bin/env python

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

import os
import random
import sys
import time

from ipf.step import Step

from mtk.amqp_0_9_1 import *

#######################################################################################################################

class AmqpPublishStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "ipf/publish/amqp"
        self.description = "publishes documents by via AMQP"
        self.time_out = 5
        self.accepts_params["services"] = "A list of services to try to connect to. Each is a dictionary with keys: host, port (optional), ssl_options (optional). The step will try to publish each document to one of these services."
        self.accepts_params["vhost"] = "the AMQP virtual host to connect to"
        self.accepts_params["exchange"] = "the AMQP exchange to publish to"
        # credentials for ssl

        self.services = []
        self.vhost = None
        self.exchange = None

        self.cur_service = None
        self.connection = None
        self.channel = None

        self.more_inputs = True

    def run(self):
        try:
            self.services = self.params["services"]
        except KeyError:
            raise StepError("services parameter not specified")
        try:
            self.vhost = self.params["vhost"]
        except KeyError:
            self.vhost = "/"
        try:
            self.exchange = self.params["exchange"]
        except KeyError:
            self.exchange = ""

        try:
            while True:
                doc = self.input_queue.get(True)
                self._publish(doc)
        except NoMoreInputsError:
            pass  # that's ok, this step is done

    def _publish(self, doc):
        self.info("publishing document of type %s",doc.type)
        self._connectIfNecessary()
        if self.channel is None:
            logger.error("not connected to any service, will not publish document of type %s",doc.type)
            return
        try:
            self.channel.basicPublish(doc.body,self.exchange,doc.id)
        except AmqpError:
            logger.warning("first publish failed, will try to another service")
            self._connect()
            self.channel.basicPublish(doc.body,self.exchange,doc.id)

    def _connectIfNecessary(self):
        if self.channel is not None:
            return
        for i in range(0,len(self.services)):
            try:
                self._connect()
                return
            except AmqpError:
                logger.warn("failed to connect to %s",self.channel["host"])

    def _connect(self):
        if self.channel is not None:
            try:
                self.channel.close()
            except AmqpError:
                pass
            self.channel = None
        if self.connection is not None:
            try:
                self.connection.close()
            except AmqpError:
                pass
            self.connection = None

        service = self._selectService()
        try:
            host = service["host"]
        except KeyError:
            host = "localhost"
        try:
            port = service["port"]
        except KeyError:
            if "ssl_options" not in service:
                port = 5672
            else:
                port = 5671
        if "ssl_options" not in service:
            self.connection = Connection(host,port,self.vhost)
        else:
            self.connection = Connection(host,port,self.vhost,X509Mechanism(),ssl_options)
        self.channel = self.connection.channel()

    def _selectService(self):
        if self.cur_service is None:
            self.cur_service = random.randint(0,len(self.services)-1)     # pick a random one the first time
        else:
            self.cur_service = (self.cur_service+1) % len(self.services)  # round robin after that
        return self.services[self.cur_service]
    
#######################################################################################################################
