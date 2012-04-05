
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

import httplib
import logging
import ConfigParser

from ipf.agent import *

logger = logging.getLogger("HttpPublishingAgent")

##############################################################################################################

class HttpPublishingAgent(Agent):

    def __init__(self, args={}):
        Agent.__init__(self,args)
        self.host = None
        self.port = None
        self.method = None
        self.path = None

    def run(self, docs_in=[]):
        try:
            self.host = self.config.get("publish_http","host")
        except ConfigParser.Error:
            logger.error("publish_http.vhost not specified")
            raise AgentError("publish_http.vhost not specified")

        try:
            self.port = self.config.getint("publish_http","port")
        except ConfigParser.Error:
            pass

        try:
            self.method = self.config.get("publish_http","method")
        except ConfigParser.Error:
            self.method = "PUT"

        try:
            self.path = self.config.get("publish_http","path")
        except ConfigParser.Error:
            pass

        connection = httplib.HTTPConnection(host+":"+str(port))
        for doc in docs_in:
            if self.path != None:
                path = self.path
            else:
                path = ""
                for part in doc.id.split(".").reverse():
                    path = path + "/" + part
            connection.request(self.method,path,doc.body,{"Content-Type": doc.content_type})
            response = httplib.getresponse()
            if not (response.status == httplib.OK or response.status == httplib.CREATED):
                logger.error("failed to '"+self.method+"' to http://"+self.host+":"+self.port+path+" - "+
                             str(response.status)+" "+response.reason)
                raise AgentError("failed to '"+self.method+"' to http://"+self.host+":"+self.port+path+" - "+
                                 str(response.status)+" "+response.reason)

        return []
