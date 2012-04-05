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
import ConfigParser

from ipf.document import Document
from ipf.error import StepError
from ipf.step import Step, StepEngine

##############################################################################################################

class LocalSoftwareStep(Step):
    def __init__(self, params={}):
        Step.__init__(self,params)

        self.name = "teragrid.local_software"
        self.description = "produces a document describing what software is installed on this resource"
        self.time_out = 15
        self.accepts_types = ["ipf/resource_name.txt"]
        self.produces_types = ["teragrid/local_software.xml"]

    def run(self):
        for doc in docs_in:
            self.warn("ignoring document of type "+doc.type)

        try:
            mechanism = self.config.get("teragrid","local_software.mechanism")
        except ConfigParser.Error:
            raise StepError("teragrid.local_software.mechanism not specified")

        if mechanism == "software_catalog":
            return self._runCatalog()
        elif mechanism == "script":
            return self._runScript()
        elif mechanism == "file":
            return self._runFile()
        else:
            raise StepError("mechanism '%s'' unknown, specify 'software_catalog', 'script', or 'file'" % mechanism)

    def _runCatalog(self):
        raise StepError("retrieving from HPC Software Catalog not yet supported")

    def _runScript(self):
        try:
            cmd = self.config.get("teragrid","local_software.script")
        except ConfigParser.Error:
            raise StepError("teragrid.local_software.script not specified")

        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError(cmd+" failed: "+output+"\n")

        doc = LocalSoftware()
        doc.body = output
        return doc

    def _runFile(self):
        try:
            file_name = self.config.get("teragrid","local_software.file")
        except ConfigParser.Error:
            raise StepError("teragrid.local_software.file not specified")

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
