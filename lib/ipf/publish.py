
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

import httplib
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

class FileStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents by writing them to a file"
        self.time_out = 5
        self._acceptParameter("path",
                              "Path to the file to write. If the path is relative, it is relative to $IPF_HOME/var/.",
                              True)


    def run(self):
        file = open(self._getPath(),"w")
        while True:
            data = self.input_queue.get(True)
            if data == None:
                break
            for rep_class in self.publish:
                if rep_class.data_cls != data.__class__:
                    continue
                rep = rep_class(data)
                self.info("writing data %s with id '%s' using representation %s",data.__class__,data.id,rep_class)
                file.write(rep.get())
                file.flush()
                break
        file.close()

    def _getPath(self):
        try:
            path = self.params["path"]
        except KeyError:
            raise StepError("path parameter not specified")
        if os.path.isabs(path):
            return path
        return os.path.join(IPF_HOME,"var",path)

#######################################################################################################################

class AmqpStep(PublishStep):
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

        try:
            self.connection.close()
        except MtkError:
            pass

    def _publish(self, representation):
        self.info("publishing representation %s",representation.__class__)
        self.debug("  with routing key '%s' to exchange '%s'",representation.data.id.encode("utf-8"),self.exchange)
        #self._connectIfNecessary()
        self._connect()
        if self.channel is None:
            raise StepError("not connected to any service, will not publish %s" % doc.__class__)
        try:
            self.channel.basicPublish(representation.get(),
                                      self.exchange,
                                      representation.data.id.encode("utf-8"))
        except MtkError:
            self.warning("first publish failed, trying again")
            try:
                self._connect()
                self.channel.basicPublish(representation.get(),
                                          self.exchange,
                                          representation.data.id.encode("utf-8"))
            except MtkError:
                raise StepError("not connected to any service, will not publish %s" % doc.__class__)
        self._close() # having some problems with connections that are open a long time without much traffic

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
            self._close()

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

    def _close(self):
        if self.connection is None:
            return
        try:
            self.connection.close()
        except:
            pass
        self.channel = None
        self.connection = None

##############################################################################################################

class HttpStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents by PUTing or POSTing them"
        self.time_out = 10
        self._acceptParameter("host","The host name of the server to publish to",True)
        self._acceptParameter("port","The port to publish to",False)
        self._acceptParameter("path","The path part of the URL",True)
        self._acceptParameter("method","PUT or POST (default PUT)",False)

    def run(self):
        try:
            host = self.params["host"]
        except KeyError:
            raise StepError("host not specified")
        try:
            port = self.params["port"]
        except KeyError:
            port = 80
        try:
            method = self.params["method"]
        except KeyError:
            method = "PUT"
        try:
            path = self.params["path"]
        except ConfigParser.Error:
            raise StepError("path not specified")

        connection = httplib.HTTPConnection(host+":"+str(port))
        while True:
            data = self.input_queue.get(True)
            if data == None:
                break
            if data.name not in self.params["representations"]:
                self.warning("no representation know for data %s with name %s",data.id,data.name)
                continue
            cls = self._getRepresentationClass(data)
            representation = cls(data)
            self.info("publishing data %s with name %s using representation %s",data.id,data.name,representation.name)

            connection.request(method,path,doc.body,{"Content-Type": representation.mime_type})
            response = httplib.getresponse()
            if not (response.status == httplib.OK or response.status == httplib.CREATED):
                self.error("failed to '"+method+"' to http://"+host+":"+port+path+" - "+
                           str(response.status)+" "+response.reason)
        connection.close()
