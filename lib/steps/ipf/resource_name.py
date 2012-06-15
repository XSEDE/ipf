#!/bin/env python

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

import socket

from ipf.document import Document
from ipf.step import Step

#######################################################################################################################

class ResourceNameStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "ipf/resource_name"
        self.description = "produces a resource name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.produces_types = ["ipf/resource_name.txt",
                               "ipf/resource_name.json",
                               "ipf/resource_name.xml"]
        self.accepts_params["resource_name"] = "a hard coded host name"

    def run(self):
        try:
            resource_name = self.params["resource_name"]
        except KeyError:
            resource_name = socket.getfqdn()

        if "ipf/resource_name.txt" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentTxt(resource_name))
        if "ipf/resource_name.json" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentJson(resource_name))
        if "ipf/resource_name.xml" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentXml(resource_name))

#######################################################################################################################

class ResourceNameDocumentTxt(Document):
    def __init__(self, resource_name):
        Document.__init__(self, resource_name, "ipf/resource_name.txt")
        self.resource_name = resource_name
        self.body = "%s\n" % resource_name

class ResourceNameDocumentJson(Document):
    def __init__(self, resource_name):
        Document.__init__(self, resource_name, "ipf/resource_name.json")
        self.resource_name = resource_name
        self.body = "{\"resourceName\": \"%s\"}\n" % resource_name

class ResourceNameDocumentXml(Document):
    def __init__(self, resource_name):
        Document.__init__(self, resource_name, "ipf/resource_name.xml")
        self.resource_name = resource_name
        self.body = "<ResourceName>%s</ResourceName>\n" % resource_name
