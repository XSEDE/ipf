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

from glue2.computing_manager import *

#######################################################################################################################

class CondorComputingManagerStep(ComputingManagerStep):

    def __init__(self, params):
        ComputingManagerStep.__init__(self,params)

        self.name = "glue2/condor/computing_manager"

    def _run(self):
        manager = ComputingManager()
        manager.ProductName = "Condor"
        manager.Name = "Condor"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################
