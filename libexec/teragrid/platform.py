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
import time
import ConfigParser

from ipf.step import Step, StepEngine
from ipf.documents.resource_name import *

#######################################################################################################################

class PlatformStep(Step):
    def __init__(self, params={}):
        Step.__init__(self,params)

        self.name = "teragrid/platform"
        self.description = "produces a platform name using tgwhatami"
        self.time_out = 5
        self.requires_types = ["ipf/resource_name.txt"]
        self.produces_types = ["teragrid/platform.txt",
                               "teragrid/platform.json",
                               "teragrid/platform.xml"]
        self.resource_name = None

    def input(self, document):
        if document.type == "ipf/resource_name.txt":
            self.resource_name = document.body.rstrip()

    def run(self):
        self.info("waiting for ipf/resource_name.txt")
        while self.resource_name == None:
            time.sleep(0.25)

        try:
            platform = self.engine.config.get("teragrid","platform")
        except ConfigParser.Error:
            try:
                tg_whatami = self.engine.config.get("teragrid","tgwhatami")
            except ConfigParser.Error:
                tg_whatami = "tgwhatami"
            (status, output) = commands.getstatusoutput(tg_whatami)
            if status != 0:
                raise StepError("failed to execute %s" % tg_whatami)
            platform = output

        if "teragrid/platform.txt" in self.requested_types:
            self.engine.output(self,PlatformDocumentTxt(self.resource_name,platform))
        if "teragrid/platform.json" in self.requested_types:
            self.engine.output(self,PlatformDocumentJson(self.resource_name,platform))
        if "teragrid/platform.xml" in self.requested_types:
            self.engine.output(self,PlatformDocumentXml(self.resource_name,platform))

#######################################################################################################################

class PlatformDocumentTxt(Document):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.txt")
        self.body = "%s\n" % platform

#######################################################################################################################

class PlatformDocumentJson(Document):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.json")
        self.type = "teragrid/platform.json"
        self.body = "{platform: \"%s\"}\n" % platform

#######################################################################################################################

class PlatformDocumentXml(Document):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.xml")
        self.body = "<Platform>%s</Platform>\n" % platform

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(PlatformStep())
