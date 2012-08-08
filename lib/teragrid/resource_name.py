
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
import socket
import sys

import ipf.name

#######################################################################################################################

class TeraGridResourceNameStep(ipf.name.ResourceNameStep):
    def __init__(self):
        ipf.name.ResourceNameStep.__init__(self)
        self.description = "produces a resource name document using tgwhereami"
        self._acceptParameter("tgwheremi","path to the tgwhereami program (default 'tgwhereami')",False)

    def run(self):
        try:
            resource_name = self.params["resource_name"]
        except KeyError:
            try:
                tg_whereami = self.params["tgwhereami"]
            except KeyError:
                tg_whereami = "tgwhereami"
            (status, output) = commands.getstatusoutput(tg_whereami)
            if status != 0:
                self.error("failed to execute %s" % tg_whereami)
                sys.exit(1)
            resource_name = output

        self._output(ResourceName(resource_name))
    
#######################################################################################################################
