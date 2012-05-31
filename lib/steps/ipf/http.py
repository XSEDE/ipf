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

import copy
import httplib
import logging
import sys

from ipf.step import Step

##############################################################################################################

class HttpPublishStep(Step):
    name = "ipf/publish/http"
    description = "publishes documents by PUTing or POSTing them"
    time_out = 10
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["requires_types"] = "The type of documents that will be published"
    accepts_params["host"] = "The host name of the server to publish to"
    accepts_params["port"] = "The port to publish to"
    accepts_params["path"] = "The path part of the URL"
    accepts_params["method"] = "PUT or POST (default PUT)"

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        try:
            host = self.params["host"]
        except KeyError:
            self.error("host not specified")
            sys.exit(1)
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
            self.error("path not specified")
            sys.exit(1)

        more_inputs = True
        connection = httplib.HTTPConnection(host+":"+str(port))
        while more_inputs:
            doc = self.input_queue.get(True)
            if doc == Step.NO_MORE_INPUTS:
                more_inputs = False
            else:
                self.info("writing document of type %s" % msg.type)
                if doc.type.endswith(".json"):
                    content_type = "application/json"
                elif doc.type.endswith(".xml"):
                    content_type = "text/xml"
                else:
                    content_type = "text/plain"
                connection.request(method,path,doc.body,{"Content-Type": content_type})
                response = httplib.getresponse()
                if not (response.status == httplib.OK or response.status == httplib.CREATED):
                    self.error("failed to '"+method+"' to http://"+host+":"+port+path+" - "+
                               str(response.status)+" "+response.reason)
