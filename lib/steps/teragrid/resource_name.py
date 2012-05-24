#!/bin/env python

###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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

import commands
import socket
import ConfigParser

from ipf.engine import StepEngine
from ipf.step import Step
from ipf.documents.resource_name import *

#######################################################################################################################

class ResourceNameStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "teragrid/resource_name"
        self.description = "produces a resource name document using tgwhereami"
        self.time_out = 5
        self.requires_types = []
        self.produces_types = ["ipf/resource_name.txt",
                               "ipf/resource_name.json",
                               "ipf/resource_name.xml"]

    def run(self):
        try:
            resource_name = self.engine.config.get("teragrid","resource_name")
        except ConfigParser.Error:
            try:
                tg_whereami = self.engine.config.get("teragrid","tgwhereami")
            except ConfigParser.Error:
                tg_whereami = "tgwhereami"
            (status, output) = commands.getstatusoutput(tg_whereami)
            if status != 0:
                raise StepError("failed to execute %s" % tg_whereami)
            resource_name = output

        if "ipf/resource_name.txt" in self.requested_types:
            self.engine.output(self,ResourceNameDocumentTxt(resource_name))
        if "ipf/resource_name.json" in self.requested_types:
            self.engine.output(self,ResourceNameDocumentJson(resource_name))
        if "ipf/resource_name.xml" in self.requested_types:
            self.engine.output(self,ResourceNameDocumentXml(resource_name))

    def input(self, document):
        self.warning("unexpected input document %s" % document.id)
        
    def noMoreInputs(self):
        pass
    
#######################################################################################################################

if __name__ == "__main__":
    StepEngine(ResourceNameStep())
