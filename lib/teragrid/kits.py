#!/usr/bin/env python

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

import commands
import logging
import os
import ConfigParser

from ipf.agent import *
from ipf.document import *
from teragrid.agent import TeraGridAgent

logger = logging.getLogger("KitsAgent")

##############################################################################################################

class KitsAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)

    def run(self, docs_in=[]):
        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        try:
            corekit_dir = self.config.get("teragrid","core_kit_directory")
        except ConfigParser.Error:
            logger.error("teragrid.core_kit_directory not specified")
            raise AgentError("teragrid.core_kit_directory not specified")

        cmd = os.path.join(corekit_dir,"bin","kits-reg.pl")
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("'"+cmd+"' failed: "+output)
            raise AgentError("'"+cmd+"' failed: "+output)

        kits = Kits()
        kits.id = self._getSystemName()
        kits.body = output

        return [kits]

##############################################################################################################

class Kits(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.Kits"
        self.content_type = "text/xml"

##############################################################################################################

if __name__ == "__main__":    
    agent = KitsAgent.createFromCommandLine()
    agent.runStdinStdout()
