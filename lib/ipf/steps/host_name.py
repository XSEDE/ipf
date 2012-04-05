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
import ConfigParser

import ipf.step
from ipf.documents.resource_name import *

#######################################################################################################################

class HostNameStep(ipf.step.Step):
    def __init__(self, params={}):
        ipf.step.Step.__init__(self,params)

        self.name = "ipf.hostname"
        self.description = "produces a resource name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.requires_types = []
        self.produces_types = ["ipf/resource_name.txt",
                               "ipf/resource_name.json",
                               "ipf/resource_name.xml"]

    def run(self):
        try:
            host_name = self.engine.config.get("default","hostname")
        except ConfigParser.NoSectionError:
            host_name = socket.gethostname()

        if "ipf/resource_name.txt" in self.requested_types:
            self.engine.output(self,ResourceNameDocumentTxt(host_name))
        if "ipf/resource_name.json" in self.requested_types:
            self.engine.output(self,ResourceNameDocumentJson(host_name))
        if "ipf/resource_name.xml" in self.requested_types:
            self.engine.output(self,ResourceNameDocumentXml(host_name))

#######################################################################################################################

if __name__ == "__main__":
    ipf.step.StepEngine(HostNameStep())
