#!/usr/bin/env python

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
import os
import time
import ConfigParser

from ipf.document import Document
from ipf.engine import StepEngine
import ipf.error
from ipf.step import Step

#######################################################################################################################

class KitsStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "teragrid.kits"
        self.description = "produces a document describing what TeraGrid kits are available on the resource"
        self.time_out = 10
        self.requires_types = ["ipf/resource_name.txt"]
        self.produces_types = ["teragrid/kits.xml"]

        self.resource_name = None

    def input(self, document):
        if document.type == "ipf/resource_name.txt":
            self.resource_name = document.body

    def run(self):
        try:
            corekit_dir = self.engine.config.get("teragrid","core_kit_directory")
        except ConfigParser.Error:
            raise ipf.error.StepError("teragrid.core_kit_directory not specified")

        cmd = os.path.join(corekit_dir,"bin","kits-reg.pl")
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("'"+cmd+"' failed: "+output)
            raise AgentError("'"+cmd+"' failed: "+output)

        self.info("waiting for ipf/resource_name.txt")
        while self.resource_name == None:
            time.sleep(0.25)

        kits = KitsDocumentXml(self.resource_name,output)

        self.engine.output(self,kits)


#######################################################################################################################

class KitsDocumentXml(Document):
    def __init__(self, resource_name, content):
        Document.__init__(self, resource_name, "teragrid/kits.xml")
        self.body = content

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(KitsStep())
