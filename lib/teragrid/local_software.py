
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

from ipf.data import Data, Representation
from ipf.step import Step
from ipf.name import ResourceName

##############################################################################################################

class LocalSoftwareStep(Step):

    def __init__(self):
        Step.__init__(self)

        self.description = "produces a document describing what software is installed on this resource"
        self.time_out = 15
        self.requires = [ResourceName]
        self.produces = [TeraGridLocalSoftware]
        self._acceptParameter("mechanism","'software_catalog', 'script', or 'file'",True)
        self._acceptParameter("script","the path to the script to use for the script mechanism",True)
        self._acceptParameter("file","the path to the file to read for the file mechanism",True)

    def run(self):
        rn = self._getInput(ResourceName)

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

        data = TeraGridLocalSoftware(output)
        self._output(self.resource_name,data)

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

class TeraGridLocalSoftware(Data):
    def __init__(self, resource_name, xml):
        Data.__init__(self)

        self.xml = xml

#######################################################################################################################

class TeraGridLocalSoftwareXml(Representation):
    data_cls = TeraGridLocalSoftware

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.data.xml

#######################################################################################################################
