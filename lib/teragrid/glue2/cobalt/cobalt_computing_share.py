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

logger = logging.getLogger("CobaltQueuesAgent")

##############################################################################################################

class CobaltQueuesAgent(ComputingSharesAgent):
    def __init__(self, args={}):
        ComputingSharesAgent.__init__(self,args)
        self.name = "teragrid.glue2.CobaltQueuesAgent"

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
        cqstat = "cqstat"
        try:
            cqstat = self.config.get("cobalt","cqstat")
        except ConfigParser.Error:
            pass
        cmd = cqstat + " -lq"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("cqstat failed: "+output)
            raise AgentError("cqstat failed: "+output+"\n")

        queueStrings = []
        curIndex = output.find("Name: ")
        if curIndex != -1:
            while True:
                nextIndex = output.find("Name: ",curIndex+1)
                if nextIndex == -1:
                    queueStrings.append(output[curIndex:])
                    break
                else:
                    queueStrings.append(output[curIndex:nextIndex])
                    curIndex = nextIndex


        queues = []
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if includeQueue(self.config,queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()
        queue.ComputingService = "http://"+self._getSystemName()+"/glue2/ComputingService/SGE"

	lines = queueString.split("\n")
	for line in lines:
            if line.startswith("Name: "):
                queue.Name = line[6:]
                queue.MappingQueue = queue.Name
                queue.ID = "http://"+self._getSystemName()+"/glue2/ComputingShare/"+queue.Name
            if line.startswith("    State"):
                state = line.split()[2]
                if state == "running":
                    queue.Extension["AcceptingJobs"] = True
                    queue.Extension["RunningJobs"] = True
                elif state == "stopped":
                    queue.Extension["AcceptingJobs"] = True
                    queue.Extension["RunningJobs"] = False
                elif state == "draining":
                    queue.Extension["AcceptingJobs"] = False
                    queue.Extension["RunningJobs"] = True
                elif state == "dead":
                    queue.Extension["AcceptingJobs"] = False
                    queue.Extension["RunningJobs"] = False
            if line.startswith("    Users"):
                # ignore user list for now
                pass
            if line.startswith("    MinTime"):
                minTime = line.split()[2]
                if minTime != "None":
                    queue.MinWallTime = queue._getDuration(minTime)
            if line.startswith("    MaxTime"):
                maxTime = line.split()[2]
                if maxTime != "None":
                    queue.MaxWallTime = queue._getDuration(maxTime)
            if line.startswith("    MaxRunning"):
                maxRunning = line.split()[2]
                if maxRunning != "None":
                    queue.Extension["MaxRunningPerUser"] = int(maxRunning)
            if line.startswith("    MaxQueued"):
                maxQueued = line.split()[2]
                if maxQueued != "None":
                    queue.Extension["MaxQueuedPerUser"] = int(maxQueued)
            if line.startswith("    MaxUserNodes"):
                maxUserNodes = line.split()[2]
                if maxUserNodes != "None":
                    queue.Extension["MaxSlotsPerUser"] = int(maxUserNodes) * coresPerNode
            if line.startswith("    TotalNodes"):
                totalNodes = line.split()[2]
                if totalNodes != "None":
                    queue.Extension["MaxSlots"] = int(totalNodes) * coresPerNode
            if line.startswith("    Priority"):
                queue.Extension["Priority"] = float(line.split()[2])
        return queue

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

##############################################################################################################

if __name__ == "__main__":
    agent = CobaltQueuesAgent.createFromCommandLine()
    agent.runStdinStdout()
