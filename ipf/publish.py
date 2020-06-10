
###############################################################################
#   Copyright 2011-2015 The University of Texas at Austin                     #
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

import http.client
import os
import random
import ssl
import sys
import threading
import time
from queue import Empty

from ipf.error import NoMoreInputsError, StepError
from ipf.paths import IPF_ETC_PATH, IPF_VAR_PATH
from ipf.step import PublishStep  # won't need in a bit
from ipf.step import TriggerStep

try:
   import amqp
except ImportError as exc:
    sys.stderr.write("Error importing amqp: Please set PYTHONPATH to include path to AMQP :"+format(exc)+"\n\n")


#######################################################################################################################

class FileStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents by writing them to a file"
        self.time_out = 5
        self._acceptParameter("path",
                              "Path to the file to write. If the path is relative, it is relative to IPF_VAR_PATH",
                              True)
        self._acceptParameter("append",
                              "Whether to append to the file or to overwrite it (default is overwrite).",
                              False)

    def _publish(self, representation):
        if self.params.get("append",False):
            self.info("appending %s",representation)
            f = open(self._getPath(),"a")
            f.write(representation.get())
            f.close()
        else:
            self.info("writing %s",representation)
            f = open(self._getPath()+".new","w")
            f.write(representation.get())
            f.close()
            os.rename(self._getPath()+".new",self._getPath())

    def _getPath(self):
        try:
            path = self.params["path"]
        except KeyError:
            raise StepError("path parameter not specified")
        if os.path.isabs(path):
            return path
        return os.path.join(IPF_VAR_PATH,path)

#######################################################################################################################

# There is a hang problem that comes up now and then, particularly with long-lived connections:
#
#   * ssl connection to server
#   * the connection is lost to the server
#     * e.g. network outage
#     * or for testing, suspending the virtual machine running the RabbitMQ service
# What happens is:
#   * the basic_publish returns, but no message is sent
#   * amqp.Connection.close() hangs
#   * heartbeats aren't being sent, so that times out
#
# Approach is to:
#   * use heartbeats to detect the connection is down
#   * call close() in a separate thread
#
# publisher confirms don't help since the wait() for the confirm could just hang

class AmqpStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents via AMQP"
        self.time_out = 5
        self._acceptParameter("services","A list of services to try to connect to. Each item is host[:port]. If no port is specified, port 5672 will be used for TCP connections and port 5671 will be used for SSL connections.",True)
        self._acceptParameter("username","the user to authenticate as",False)
        self._acceptParameter("password","the password to authenticate with",False)
        self._acceptParameter("ssl_options","A dictionary containing the SSL options to use to connect. See the Python ssl.wrap_socket function for keys and values. Any relative path names are relative to a path in $IPF_WORKFLOW_PATH",False)
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
        if "ssl_options" in self.params:
            self.ssl_options = {}
            for (key,value) in self.params["ssl_options"].items():
                self.ssl_options[key] = value
            try:
                if not os.path.isabs(self.ssl_options["keyfile"]):
                    self.ssl_options["keyfile"] = os.path.join(IPF_ETC_PATH,self.ssl_options["keyfile"])
            except KeyError:
                pass
            try:
                if not os.path.isabs(self.ssl_options["certfile"]):
                    self.ssl_options["certfile"] = os.path.join(IPF_ETC_PATH,self.ssl_options["certfile"])
            except KeyError:
                pass
            try:
                if not os.path.isabs(self.ssl_options["ca_certs"]):
                    self.ssl_options["ca_certs"] = os.path.join(IPF_ETC_PATH,self.ssl_options["ca_certs"])
            except KeyError:
                pass
            if "ca_certs" in self.ssl_options and "cert_reqs" not in self.ssl_options:
                self.ssl_options["cert_reqs"] = ssl.CERT_REQUIRED

        try:
            self.vhost = self.params["vhost"].encode("utf-8")
        except KeyError:
            self.vhost = "/"
        try:
            self.exchange = self.params["exchange"].encode("utf-8")
        except KeyError:
            self.exchange = ""

        # don't use PublishStep.run since we need to handle AMQP heartbeats
        while True:
            try:
                data = self.input_queue.get(True,5)
                if data == None:
                    break
                for rep_class in self.publish:
                    if rep_class.data_cls != data.__class__:
                        continue
                    rep = rep_class(data)
                    self._publish(rep)
                    break
            except Empty:
                pass
            if self.connection is None:
                continue

            # quick wait with no allowed_mthods to get heartbeats from the server
            #   hack since amqp.Connection.wait() doesn't have a timeout argument
            try:
                self.connection._wait_multiple({self.channel.channel_id:self.channel},[],1)
            except:
                # timeouts are expected
                pass

            try:
                self.connection.heartbeat_tick()
            except amqp.ConnectionForced:
                self.warning("closing connection - missed too many heartbeats")
                self._close()

        self._close()

    def _publish(self, representation):
        self.info("publishing %s",representation)
        self.debug("  with routing key '%s' to exchange '%s'",representation.data.id,self.exchange)
        try:
            self._publishOnce(representation)
        except Exception as e:
            self.info("first publish failed: %s",e)
            try:
                self._publishOnce(representation)
            except Exception as e:
                self.error("publishing failed twice - discarding data: %s",e)

    def _publishOnce(self, representation):
        try:
            self._connectIfNecessary()
        except StepError:
            raise StepError("not connected to any service, will not publish %s" % representation.__class__)
        try:
            self.channel.basic_publish(amqp.Message(body=representation.get()),
                                       self.exchange,
                                       representation.data.id.encode("utf-8"))
        except Exception as e:
            self._close()
            raise StepError("failed to publish %s: %s" % (representation.__class__,e))

    def _connectIfNecessary(self):
        if self.channel is not None:
            return
        for i in range(0,len(self.services)):
            service = self._selectService()
            try:
                self._connect(service)
                return
            except Exception as e:
                self.warning("failed to connect to service %s: %s",service,e)
        raise StepError("could not connect to any of the specified messaging services")

    def _connect(self, service):
        if self.connection is not None:
            self._close()

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
            ssl = False
            login_method = "AMQPLAIN"
        else:
            ssl = self.ssl_options
            if "certfile" in ssl:
                login_method = "EXTERNAL"
            else:
                login_method = "AMQPLAIN"

        self.connection = amqp.Connection(host="%s:%d" % (host,port),
                                          login_method=login_method,
                                          userid=self.username,
                                          password=self.password,
                                          virtual_host=self.vhost,
                                          ssl=ssl,
                                          heartbeat=60,
                                          confirm_publish=True)
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
        # call close in a thread in case it takes a long time (e.g. network outage)
        thread = _AmqpConnectionClose(self.connection)
        self.channel = None
        self.connection = None
        thread.start()
        thread.join(5)
        if thread.isAlive():
            self.warning("close didn't finish quickly")

class _AmqpConnectionClose(threading.Thread):
    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.daemon = True
        self.connection = connection

    def run(self):
        try:
            self.connection.close()
        except:
            pass


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
            self.host = self.params["host"]
        except KeyError:
            raise StepError("host not specified")
        try:
            self.port = self.params["port"]
        except KeyError:
            self.port = 80
        try:
            self.method = self.params["method"]
        except KeyError:
            self.method = "PUT"
        try:
            self.path = self.params["path"]
        except ConfigParser.Error:
            raise StepError("path not specified")

        PublishStep.run(self)

    def _publish(self, representation):
        self.info("publishing %s",representation)
        connection = http.client.HTTPConnection(self.host+":"+str(self.port))
        connection.request(self.method,self.path,representation.get(),{"Content-Type": representation.mime_type})
        response = http.client.getresponse()
        if not (response.status == http.client.OK or response.status == http.client.CREATED):
            self.error("failed to '"+self.method+"' to http://"+self.host+":"+self.port+self.path+" - "+
                       str(response.status)+" "+response.reason)
        connection.close()


#######################################################################################################################

# mostly for debugging
class PrintStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents by writing them to stdout"
        self.time_out = 5

    def _publish(self, representation):
        print(representation.get())

#######################################################################################################################
