
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

import ipf.platform

#######################################################################################################################

class PlatformStep(ipf.platform.PlatformStep):

    def __init__(self):
        ipf.platform.PlatformStep.__init__(self)
        self._acceptParameter("tgwhatami","path to the tgwhatami program (default 'tgwhatami')",False)

    def run(self):
        try:
            tg_whatami = self.params["tgwhatami"]
        except KeyError:
            tg_whatami = "tgwhatami"
        (status, output) = commands.getstatusoutput(tg_whatami)
        if status != 0:
            raise StepError("failed to execute %s" % tg_whatami)
        return output

#######################################################################################################################
