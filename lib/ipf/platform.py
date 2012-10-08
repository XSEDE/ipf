
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

import platform

from ipf.data import Data, Representation
from ipf.error import StepError
from ipf.name import ResourceName
from ipf.step import Step

#######################################################################################################################

class PlatformStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "Produces a platform string."
        self.time_out = 10
        self.requires = [ResourceName]
        self.produces = [Platform]
        self._acceptParameter("platform","A hard-coded platform string",False)

    def run(self):
        resource_name = self._getInput(ResourceName).resource_name
        try:
            plat = self.params["platform"]
        except KeyError:
            self._output(Platform(resource_name,self._run()))
        else:
            self._output(Platform(resource_name,plat))

    def _run(self):
        os = platform.system().lower()
        (name,version,id) = platform.linux_distribution()
        distribution = name.lower() + version[0]
        arch = platform.processor()
        return "%s-%s-%s" % (os,distribution,arch)

#######################################################################################################################

class Platform(Data):
    def __init__(self, id, plat):
        Data.__init__(self,id)
        self.platform = plat

    def __str__(self):
        return "%s" % self.platform

#######################################################################################################################

class PlatformTxt(Representation):
    data_cls = Platform

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.platform

#######################################################################################################################
