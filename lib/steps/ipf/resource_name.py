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

import copy
import socket

from ipf.document import Document
from ipf.step import Step

#######################################################################################################################

class ResourceNameStep(Step):
    name = "ipf/hostname"
    description = "produces a resource name document using the fully qualified domain name of the host"
    time_out = 5
    produces_types = ["ipf/resource_name.txt",
                      "ipf/resource_name.json",
                      "ipf/resource_name.xml"]
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["hostname"] = "a hard coded host name"

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        try:
            host_name = self.accepts_params["hostname"]
        except KeyError:
            host_name = socket.getfqdn()

        if "ipf/resource_name.txt" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentTxt(host_name))
        if "ipf/resource_name.json" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentJson(host_name))
        if "ipf/resource_name.xml" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentXml(host_name))

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
