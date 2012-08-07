
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
import logging
import sys

from ipf.error import StepError
from ipf.step import PublishStep

##############################################################################################################

class HttpPublishStep(PublishStep):
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
