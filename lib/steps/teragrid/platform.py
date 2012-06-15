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
import sys

from ipf.document import Document
from ipf.step import Step

#######################################################################################################################

class PlatformStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "teragrid/platform"
        self.description = "produces a platform name using tgwhatami"
        self.time_out = 5
        self.requires_types = ["ipf/resource_name.txt"]
        self.produces_types = ["teragrid/platform.txt",
                               "teragrid/platform.json",
                               "teragrid/platform.xml"]
        self.accepts_params["tgwhatami"] = "path to the tgwhatami program (default 'tgwhatami')"
        self.accepts_params["platform"] = "hard coded name of the TeraGrid platform (optional)"

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")

        try:
            platform = self.params["platform"]
        except KeyError:
            try:
                tg_whatami = self.params["tgwhatami"]
            except KeyError:
                tg_whatami = "tgwhatami"
            (status, output) = commands.getstatusoutput(tg_whatami)
            if status != 0:
                self.error("failed to execute %s" % tg_whatami)
                sys.exit(1)
            platform = output

        if "teragrid/platform.txt" in self.requested_types:
            self.output_queue.put(PlatformDocumentTxt(rn_doc.body,platform))
        if "teragrid/platform.json" in self.requested_types:
            self.output_queue.put(PlatformDocumentJson(rn_doc.body,platform))
        if "teragrid/platform.xml" in self.requested_types:
            self.output_queue.put(PlatformDocumentXml(rn_doc.body,platform))

#######################################################################################################################

class PlatformDocumentTxt(Document):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.txt")
        self.platform = platform
        self.body = "%s\n" % platform

#######################################################################################################################

class PlatformDocumentJson(Document):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.json")
        self.platform = platform
        self.body = "{platform: \"%s\"}\n" % platform

#######################################################################################################################

class PlatformDocumentXml(Document):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.xml")
        self.platform = platform
        self.body = "<Platform>%s</Platform>\n" % platform

#######################################################################################################################
