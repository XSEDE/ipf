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

from steps.ipf.site_name import *
from ipf.step import Step

#######################################################################################################################

class SiteNameStep(Step):
    name = "teragrid/site_name"
    description = "produces a site name document using tgwhereami"
    time_out = 5
    requires_types = []
    produces_types = ["ipf/site_name.txt",
                      "ipf/site_name.json",
                      "ipf/site_name.xml"]
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["tgwheremi"] = "path to the tgwhereami program (default 'tgwhereami')"
    accepts_params["site_name"] = "hard coded name of the TeraGrid site name (optional)"

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        try:
            site_name = self.params["site_name"]
        except KeyError:
            try:
                tg_whereami = self.params["tgwhereami"]
            except KeyError:
                tg_whereami = "tgwhereami"
            (status, output) = commands.getstatusoutput(tg_whereami+" -s")
            if status != 0:
                self.error("failed to execute %s" % tg_whereami)
                sys.exit(1)
            site_name = output

        if "ipf/site_name.txt" in self.requested_types:
            self.output_queue.put(SiteNameDocumentTxt(site_name))
        if "ipf/site_name.json" in self.requested_types:
            self.output_queue.put(SiteNameDocumentJson(site_name))
        if "ipf/site_name.xml" in self.requested_types:
            self.output_queue.put(SiteNameDocumentXml(site_name))

#######################################################################################################################
