#!/usr/bin/env python

###############################################################################
#   Copyright 2011 The University of Texas at Austin                          #
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

from ipf.step import StepEngine

from teragrid.glue2.computing_service import *

#######################################################################################################################

class SgeComputingServiceStep(ComputingServiceStep):
    def __init__(self, params={}):
        ComputingServiceStep.__init__(self,params)
        self.name = "glue2/sge/computing_service"

    def _run(self):
        service = ComputingService()
        service.Name = "SGE"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.SGE"
        service.QualityLevel = "production"

        return service
        
##############################################################################################################

if __name__ == "__main__":    
    StepEngine(SgeComputingServiceStep())
