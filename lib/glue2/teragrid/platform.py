
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

import copy

from teragrid.platform import TeraGridPlatform

class PlatformMixIn(object):
    """Assumes that it is being mixed in with a Step."""

    def __init__(self):
        self.requires.append(TeraGridPlatform)
        self.platform = None

    def addTeraGridPlatform(self, environments):
        self.platform = self._getInput(TeraGridPlatform).platform
        for env in environments:
            env.Extension["TeraGridPlatform"] = self.platform
