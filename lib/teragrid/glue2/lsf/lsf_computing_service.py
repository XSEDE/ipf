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

import logging

from teragrid.glue2.computing_service import *

logger = logging.getLogger("LsfComputingServiceAgent")

##############################################################################################################

class LsfComputingServiceAgent(ComputingServiceAgent):
    def __init__(self, args={}):
        ComputingServiceAgent.__init__(self,args)
        self.name = "teragrid.glue2.LsfComputingService"

    def run(self, docs_in=[]):
        logger.info("running")

        service = ComputingService()
        service.Name = "LSF"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.LSF"
        service.QualityLevel = "production"

        service.ID = "http://"+self._getSystemName()+"/glue2/ComputingService/"+service.Name
        service.ComputingManager = "http://"+self._getSystemName()+"/glue2/ComputingManager/"+service.Name

        for doc in docs_in:
            if doc.type == "teragrid.glue2.ComputingShare":
                self._addShare(service,doc)
            elif doc.type == "teragrid.glue2.ComputingEndpoint":
                service.ComputingEndpoint.append(doc.ID)
            else:
                logger.warn("ignoring document of type "+doc.type)

        service.id = self._getSystemName()

        return [service]
        
##############################################################################################################

if __name__ == "__main__":    
    agent = LsfComputingServiceAgent.createFromCommandLine()
    agent.runStdinStdout()
