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

logger = logging.getLogger("PbsQueuesAgent")

##############################################################################################################

class PbsQueuesAgent(ComputingSharesAgent):
    def __init__(self, args={}):
        ComputingSharesAgent.__init__(self,args)
        self.name = "teragrid.glue2.PbsQueuesAgent"

    def run(self, docs_in=[]):
        logger.info("running")
        queues = self._getQueues()

        activities = []
        for doc in docs_in:
            if doc.type == "teragrid.glue2.ComputingActivity":
                activities.append(doc)
            else:
                logger.warn("ignoring document of type "+doc.type)
        self._addActivities(activities,queues)

        for queue in queues:
            queue.id = queue.MappingQueue+"."+self._getSystemName()

        return queues

    def _getQueues(self):
        qstat = "qstat"
        try:
            qstat = self.config.get("pbs","qstat")
        except ConfigParser.Error:
            pass
        cmd = qstat + " -q -G"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("qstat failed: "+output)
            raise AgentError("qstat failed: "+output+"\n")


        queueStrings = output.split("\n")
        queueStrings = queueStrings[5:len(queueStrings)-2]

        queues = []
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if includeQueue(self.config,queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()
        queue.ComputingService = "http://"+self._getSystemName()+"/glue2/ComputingService"

        (queueName,
         memoryLimitGB,
         cpuTimeLimit,
         wallTimeLimit,
         nodeLimit,
         runningJobs,
         queuedJobs,
         maxRunningJobs,
         enableDisable,
         runningStopped) = queueString.split()

        queue.Name = queueName
        queue.MappingQueue = queue.Name
        queue.ID = "http://"+self._getSystemName()+"/glue2/ComputingShare/"+queue.Name
        if cpuTimeLimit != "--":
            queue.MaxTotalCPUTime = self._getDuration(cpuTimeLimit)
        if wallTimeLimit != "--":
            queue.MaxWallTime = self._getDuration(wallTimeLimit)
        if nodeLimit != "--":
            queue.MaxSlotsPerJob = int(nodeLimit)
        queue.TotalJobs = 0
        if runningJobs != "--":
            queue.LocalRunningJobs = int(runningJobs)
            queue.RunningJobs = queue.LocalRunningJobs
            queue.TotalJobs = queue.TotalJobs + queue.RunningJobs
        if queuedJobs != "--":
            queue.LocalWaitingJobs = int(queuedJobs)
            queue.WaitingJobs = queue.LocalWaitingJobs
            queue.TotalJobs = queue.TotalJobs + queue.WaitingJobs
        if maxRunningJobs != "--":
            queue.MaxRunningJobs = int(maxRunningJobs)
        if enableDisable == "E":
            queue.Extension["AcceptingJobs"] = True
        else:
            queue.Extension["AcceptingJobs"] = False
        if runningStopped == "R":
            queue.Extension["RunningJobs"] = True
        else:
            queue.Extension["RunningJobs"] = False

        return queue


    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

##############################################################################################################

if __name__ == "__main__":
    agent = PbsQueuesAgent.createFromCommandLine()
    agent.runStdinStdout()
