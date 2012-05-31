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
import copy
import socket
import sys

from steps.ipf.resource_name import *
import ipf.step

#######################################################################################################################

class ResourceNameStep(ipf.step.Step):
    name = "teragrid/resource_name"
    description = "produces a resource name document using tgwhereami"
    time_out = 5
    produces_types = ["ipf/resource_name.txt",
                      "ipf/resource_name.json",
                      "ipf/resource_name.xml"]
    accepts_params = copy.copy(ipf.step.Step.accepts_params)
    accepts_params["tgwheremi"] = "path to the tgwhereami program (default 'tgwhereami')"
    accepts_params["resource_name"] = "hard coded name of the TeraGrid resource name (optional)"

    def __init__(self, params):
        ipf.step.Step.__init__(self,params)

    def run(self):
        try:
            resource_name = self.params["resource_name"]
        except KeyError:
            try:
                tg_whereami = self.params["tgwhereami"]
            except KeyError:
                tg_whereami = "tgwhereami"
            (status, output) = commands.getstatusoutput(tg_whereami)
            if status != 0:
                self.error("failed to execute %s" % tg_whereami)
                sys.exit(1)
            resource_name = output

        if "ipf/resource_name.txt" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentTxt(resource_name))
        if "ipf/resource_name.json" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentJson(resource_name))
        if "ipf/resource_name.xml" in self.requested_types:
            self.output_queue.put(ResourceNameDocumentXml(resource_name))
    
#######################################################################################################################
