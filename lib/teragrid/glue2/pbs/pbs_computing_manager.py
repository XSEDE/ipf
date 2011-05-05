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

from teragrid.glue2.computing_manager import *

logger = logging.getLogger("PbsComputingManagerAgent")

##############################################################################################################

class PbsComputingManagerAgent(ComputingManagerAgent):
    def __init__(self, args={}):
        ComputingManagerAgent.__init__(self,args)
        self.name = "teragrid.glue2.PbsComputingManager"

    def run(self, docs_in=[]):
        logger.info("running")

        manager = ComputingManager()
        manager.ProductName = "PBS"
        manager.Name = "PBS"
        manager.Reservation = True
        #self.BulkSubmission = True
        manager.ID = "http://"+self._getSystemName()+"/glue2/ComputingManager/"+manager.Name

        for doc in docs_in:
            if doc.type == "teragrid.glue2.ComputingService":
                manager.ComputingService = doc.ID
            elif doc.type == "teragrid.glue2.ExecutionEnvironment":
                manager._addExecutionEnvironment(doc)
            elif doc.type == "teragrid.glue2.ComputingShare":
                manager._addComputingShare(doc)
            else:
                logger.warn("ignoring document of type "+doc.type)

        manager.id = self._getSystemName()

        return [manager]

##############################################################################################################

if __name__ == "__main__":    
    agent = PbsComputingManagerAgent.createFromCommandLine()
    agent.runStdinStdout()
