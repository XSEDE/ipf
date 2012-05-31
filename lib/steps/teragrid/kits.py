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
import copy
import os
import sys
import time

from ipf.document import Document
from ipf.step import Step

#######################################################################################################################

class KitsStep(Step):

    name = "teragrid.kits"
    description = "produces a document describing what TeraGrid kits are available on the resource"
    time_out = 10
    requires_types = ["ipf/resource_name.txt"]
    produces_types = ["teragrid/kits.xml"]
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["core_kit_directory"] = "the path to the TeraGrid core kit installation"

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        
        try:
            corekit_dir = self.params["core_kit_directory"]
        except KeyError:
            self.error("core_kit_directory not specified")
            sys.exit(1)

        cmd = os.path.join(corekit_dir,"bin","kits-reg.pl")
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("'"+cmd+"' failed: "+output)
            sys.exit(1)

        kits = KitsDocumentXml(rn_doc.body,output)

        self.output_queue.put(kits)


#######################################################################################################################

class KitsDocumentXml(Document):
    def __init__(self, resource_name, content):
        Document.__init__(self, resource_name, "teragrid/kits.xml")
        self.body = content

#######################################################################################################################
