
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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
import ssl
import sys
import time

from ipf.error import NoMoreInputsError, StepError
from ipf.home import IPF_HOME
from ipf.step import PublishStep

from mtk.amqp_0_9_1 import *

#######################################################################################################################

class AmqpPublishStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents via AMQP"
        self.time_out = 5
        self._acceptParameter("services","A list of services to try to connect to. Each item is host[:port]. If no port is specified, port 5672 will be used for TCP connections and port 5671 will be used for SSL connections.",True)
        self._acceptParameter("username","the user to authenticate as",False)
        self._acceptParameter("password","the password to authenticate with",False)
        self._acceptParameter("ssl_options","A dictionary containing the SSL options to use to connect. See the Python ssl.wrap_socket function for keys and values. Any relative path names are relative to $IPF_HOME/etc",False)
        self._acceptParameter("vhost","the AMQP virtual host to connect to",False)
        self._acceptParameter("exchange","the AMQP exchange to publish to",False)

        self.services = []
        self.username = None
        self.password = None
        self.ssl_options = None
        self.vhost = None
        self.exchange = None

        self.cur_service = None
        self.connection = None
        self.channel = None

    def run(self):
        try:
            self.services = self.params["services"]
        except KeyError:
            raise StepError("services parameter not specified")
        try:
            self.username = self.params["username"].encode("utf-8")
        except KeyError:
            self.username = "guest"
        try:
            self.password = self.params["password"].encode("utf-8")
        except KeyError:
            self.password = "guest"
        try:
            self.ssl_options = self.params["ssl_options"]
            try:
                if not os.path.isabs(self.ssl_options["keyfile"]):
                    self.ssl_options["keyfile"] = os.path.join(IPF_HOME,"etc",self.ssl_options["keyfile"])
            except KeyError:
                pass
            try:
                if not os.path.isabs(self.ssl_options["certfile"]):
                    self.ssl_options["certfile"] = os.path.join(IPF_HOME,"etc",self.ssl_options["certfile"])
            except KeyError:
                pass
            try:
                if not os.path.isabs(self.ssl_options["ca_certs"]):
                    self.ssl_options["ca_certs"] = os.path.join(IPF_HOME,"etc",self.ssl_options["ca_certs"])
            except KeyError:
                pass
            if "ca_certs" in self.ssl_options and "cert_reqs" not in self.ssl_options:
                self.ssl_options["cert_reqs"] = ssl.CERT_REQUIRED
        except KeyError:
            self.ssl_options = None

        try:
            self.vhost = self.params["vhost"].encode("utf-8")
        except KeyError:
            self.vhost = "/"
        try:
            self.exchange = self.params["exchange"].encode("utf-8")
        except KeyError:
            self.exchange = ""

        while True:
            data = self.input_queue.get(True)
            if data == None:
                break
            for rep_class in self.publish:
                if rep_class.data_cls != data.__class__:
                    continue
                rep = rep_class(data)
                self._publish(rep)
                break

    def _publish(self, representation):
        self.info("publishing representation %s",representation.__class__)
        self.debug("  with routing key '%s' to exchange '%s'",representation.data.id.encode("utf-8"),self.exchange)
        self._connectIfNecessary()
        if self.channel is None:
            raise StepError("not connected to any service, will not publish %s" % doc.__class__)
        try:
            self.channel.basicPublish(representation.get(),
                                      self.exchange,
                                      representation.data.id.encode("utf-8"))
        except MtkError:
            self.warning("first publish failed, will try to another service")
            try:
                self._connect()
                self.channel.basicPublish(representation.get(),
                                          self.exchange,
                                          representation.data.id.encode("utf-8"))
            except MtkError:
                raise StepError("not connected to any service, will not publish %s" % doc.__class__)

    def _connectIfNecessary(self):
        if self.channel is not None:
            return
        for i in range(0,len(self.services)):
            try:
                self._connect()
                return
            except MtkError, e:
                self.warning("failed to connect to service: %s",e)
        raise StepError("could not connect to any of the specified messaging services")

    def _connect(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
            self.channel = None

        service = self._selectService()
        toks = service.split(":")
        host = toks[0]
        try:
            port = int(toks[1])
        except:
            if self.ssl_options is None:
                port = 5672
            else:
                port = 5671
                
        if self.ssl_options is None:
            self.connection = Connection(host,
                                         port,
                                         self.vhost,
                                         PlainMechanism(self.username,self.password))
        else:
            if "keyfile" in self.ssl_options:
                self.connection = Connection(host,
                                             port,
                                             self.vhost,
                                             X509Mechanism(),
                                             self.ssl_options)
            else:
                self.connection = Connection(host,
                                             port,
                                             self.vhost,
                                             PlainMechanism(self.username,self.password),
                                             self.ssl_options)
        self.channel = self.connection.channel()

    def _selectService(self):
        if self.cur_service is None:
            self.cur_service = random.randint(0,len(self.services)-1)     # pick a random one the first time
        else:
            self.cur_service = (self.cur_service+1) % len(self.services)  # round robin after that
        return self.services[self.cur_service]
    
#######################################################################################################################
