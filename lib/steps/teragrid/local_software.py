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
import logging
import os
import sys

from ipf.document import Document
from ipf.step import Step

##############################################################################################################

class LocalSoftwareStep(Step):
    name = "teragrid.local_software"
    description = "produces a document describing what software is installed on this resource"
    time_out = 15
    requires_types = ["ipf/resource_name.txt"]
    produces_types = ["teragrid/local_software.xml"]
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["mechanism"] = "'software_catalog', 'script', or 'file'"
    accepts_params["script"] = "the path to the script to use for the script mechanism"
    accepts_params["file"] = "the path to the file to read for the file mechanism"

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")

        try:
            mechanism = self.params["mechanism"]
        except KeyError:
            self.error("mechanism not specified")
            sys.exit(1)

        if mechanism == "software_catalog":
            return self._runCatalog()
        elif mechanism == "script":
            return self._runScript()
        elif mechanism == "file":
            return self._runFile()
        else:
            self.error("mechanism '%s'' unknown, specify 'software_catalog', 'script', or 'file'" % mechanism)
            sys.exit(1)

    def _runCatalog(self):
        self.error("retrieving from HPC Software Catalog not yet supported")
        sys.exit(1)

    def _runScript(self):
        try:
            cmd = self.params["script"]
        except KeyError:
            self.error("script not specified")
            sys.exit(1)

        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error(cmd+" failed: "+output+"\n")
            sys.exit(1)

        doc = LocalSoftware()
        doc.body = output
        return doc

    def _runFile(self):
        try:
            file_name = self.params["file"]
        except KeyError:
            self.error("file not specified")
            sys.exit(1)

        doc = LocalSoftware()
        file = open(file_name,"r")
        doc.body = file.read()
        file.close()
        return doc

##############################################################################################################

class LocalSoftwareDocumentXml(Document):
    def __init__(self, resource_name, content):
        Document.__init__(self, resource_name, "teragrid.local_software")
        self.body = content

##############################################################################################################

if __name__ == "__main__":
    StepEngine(LocalSoftwareStep())
