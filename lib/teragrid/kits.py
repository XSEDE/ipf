
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
import sys
import time

from ipf.data import Data, Representation
from ipf.error import StepError
from ipf.name import ResourceName
from ipf.step import Step

#######################################################################################################################

class KitsStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces data describing what TeraGrid kits are available on the resource"
        self.time_out = 10
        self.requires = [ResourceName]
        self.produces = [Kits]
        self._acceptParameter("core_kit_directory","the path to the TeraGrid core kit installation",True)

    def run(self):
        resource_name = self._getInput(ResourceName).resource_name
        
        try:
            corekit_dir = self.params["core_kit_directory"]
        except KeyError:
            raise StepError("core_kit_directory not specified")

        cmd = os.path.join(corekit_dir,"bin","kits-reg.pl")
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("'%s' failed: %s" % (cmd,output))

        self._output(Kits(resource_name,kits))

#######################################################################################################################

class Kits(Data):
    def __init__(self, resource_name, kits):
        Data.__init__(self,resource_name)
        self.kits = kits

#######################################################################################################################

class KitsXml(Representation):
    data_cls = Kits

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.data.kits

#######################################################################################################################
