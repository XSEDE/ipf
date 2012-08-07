
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

from glue2.computing_manager import *

#######################################################################################################################

class NimbusComputingManagerStep(ComputingManagerStep):
    def __init__(self):
        ComputingManagerStep.__init__(self)

        self._acceptParameter("nimbus_version","the Nimbus version",False)

    def _run(self):
        manager = ComputingManager()
        manager.ProductName = "Nimbus"
        manager.Name = "Nimbus"
        manager.Reservation = False
        manager.BulkSubmission = True

        try:
            manager.Version = self.params["nimbus_version"]
        except KeyError:
            pass

        return manager

#######################################################################################################################
