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

import commands
import logging
import os
import socket
import sys

from ipf.error import *
from teragrid.glue2.computing_share import *
from teragrid.glue2.computing_activity import *

logger = logging.getLogger("CondorQueuesAgent")

##############################################################################################################

#arg.defaultValue = "qconf"
#arg.description = "The path to the CONDOR qconf program. Only needed if 'qconf' won't execute."

##############################################################################################################

class CondorQueuesAgent(ComputingSharesAgent):
    def __init__(self, args={}):
        ComputingSharesAgent.__init__(self,args)
        self.name = "teragrid.glue2.CondorQueuesAgent"

    def run(self, docs_in=[]):
        logger.info("running")
        queues = self._getQueues()

        activities = []
        for doc in docs_in:
            if doc.type == "teragrid.glue2.ComputingActivity":
                activities.append(doc)
            else:
                logger.warn("ignoring document of type "+doc.type)
        # bit of a hack, but easy
        for activity in activities:
            activity.Queue = "condor"
        self._addActivities(activities,queues)

        for queue in queues:
            queue.id = queue.MappingQueue+"."+self._getSystemName()

        return queues

    def _getQueues(self):
        queue = ComputingShare()
        queue.ComputingService = "http://"+self._getSystemName()+"/glue2/ComputingService"

        queue.Name = "condor"
        queue.MappingQueue = "condor"
        queue.ID = "http://"+self._getSystemName()+"/glue2/ComputingShare/"+queue.Name
        #queue.MaxSlotsPerJob = 1

        return [queue]

##############################################################################################################

if __name__ == "__main__":
    agent = CondorQueuesAgent.createFromCommandLine()
    agent.runStdinStdout()
