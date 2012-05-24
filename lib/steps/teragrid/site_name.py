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

from ipf.documents.site_name import *
from ipf.engine import StepEngine
from ipf.step import Step

#######################################################################################################################

class SiteNameStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "teragrid/site_name"
        self.description = "produces a site name document using tgwhereami"
        self.time_out = 5
        self.requires_types = []
        self.produces_types = ["ipf/site_name.txt",
                               "ipf/site_name.json",
                               "ipf/site_name.xml"]

    def run(self):
        try:
            site_name = self.engine.config.get("teragrid","site_name")
        except ConfigParser.Error:
            try:
                tg_whereami = self.engine.config.get("teragrid","tgwhereami")
            except ConfigParser.Error:
                tg_whereami = "tgwhereami"
            (status, output) = commands.getstatusoutput(tg_whereami+" -s")
            if status != 0:
                raise StepError("failed to execute %s" % tg_whereami)
            site_name = output

        if "ipf/site_name.txt" in self.requested_types:
            self.engine.output(self,SiteNameDocumentTxt(site_name))
        if "ipf/site_name.json" in self.requested_types:
            self.engine.output(self,SiteNameDocumentJson(site_name))
        if "ipf/site_name.xml" in self.requested_types:
            self.engine.output(self,SiteNameDocumentXml(site_name))

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(SiteNameStep())
