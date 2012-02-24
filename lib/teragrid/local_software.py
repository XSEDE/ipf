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

logger = logging.getLogger("LocalSoftwareAgent")

##############################################################################################################

class LocalSoftwareAgent(Agent):
    def __init__(self, args={}):
        Agent.__init__(self,args)

    def run(self, docs_in=[]):
        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        try:
            mechanism = self.config.get("local_software","mechanism")
        except ConfigParser.Error:
            logger.error("local_software.mechanism not specified")
            raise AgentError("local_software.mechanism not specified")

        if mechanism == "software_catalog":
            return self._runCatalog()
        elif mechanism == "script":
            return self._runScript()
        elif mechanism == "file":
            return self._runFile()
        else:
            raise AgentError("mechanism '"+mechanism+"' unknown, specify software_catalog, script, or file")

    def _runCatalog(self):
        raise AgentError("retrieving from HPC Software Catalog not yet supported")

    def _runScript(self):
        try:
            cmd = self.config.get("local_software","script")
        except ConfigParser.Error:
            logger.error("local_software.cmd not specified")
            raise AgentError("local_software.cmd not specified")

        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error(cmd+" failed: "+output)
            raise AgentError(cmd+" failed: "+output+"\n")

        doc = LocalSoftware()
        doc.body = output
        return doc

    def _runFile(self):
        try:
            file_name = self.config.get("local_software","file")
        except ConfigParser.Error:
            logger.error("local_software.file not specified")
            raise AgentError("local_software.file not specified")

        doc = LocalSoftware()
        file = open(file_name,"r")
        doc.body = file.read()
        file.close()
        return doc

##############################################################################################################

class LocalSoftware(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.LocalSoftware"
        self.content_type = "text/xml"

##############################################################################################################

if __name__ == "__main__":    
    agent = LocalSoftwareAgent.createFromCommandLine()
    agent.runStdinStdout()
