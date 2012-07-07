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
import logging
import os
import sys

from ipf.document import Document
from ipf.step import Step

##############################################################################################################

class LocalSoftwareStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "teragrid.local_software"
        self.description = "produces a document describing what software is installed on this resource"
        self.time_out = 15
        self.requires_types = ["ipf/resource_name.txt"]
        self.produces_types = ["teragrid/local_software.xml"]
        self.accepts_params["mechanism"] = "'software_catalog', 'script', or 'file'"
        self.accepts_params["script"] = "the path to the script to use for the script mechanism"
        self.accepts_params["file"] = "the path to the file to read for the file mechanism"

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")

        try:
            mechanism = self.params["mechanism"]
        except KeyError:
            self.error("mechanism not specified")
            sys.exit(1)

        if mechanism == "software_catalog":
            self._runCatalog()
        elif mechanism == "script":
            self._runScript()
        elif mechanism == "file":
            self._runFile()
        else:
            raise StepError("mechanism '%s'' unknown, specify 'software_catalog', 'script', or 'file'" % mechanism)

    def _runCatalog(self):
        raise StepError("retrieving from HPC Software Catalog not yet supported")

    def _runScript(self):
        try:
            cmd = self.params["script"]
        except KeyError:
            raise StepError("script not specified")

        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError(cmd+" failed: "+output+"\n")

        doc = LocalSoftware()
        doc.body = output
        self._output(doc)

    def _runFile(self):
        try:
            file_name = self.params["file"]
        except KeyError:
            raise StepError("file not specified")

        doc = LocalSoftware()
        file = open(file_name,"r")
        doc.body = file.read()
        file.close()
        self._output(doc)

#######################################################################################################################

class LocalSoftwareDocumentXml(Document):
    def __init__(self, resource_name, content):
        Document.__init__(self, resource_name, "teragrid.local_software")
        self.body = content

#######################################################################################################################
