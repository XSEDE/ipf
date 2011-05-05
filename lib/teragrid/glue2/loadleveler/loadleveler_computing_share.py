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

logger = logging.getLogger("LoadLevelerQueuesAgent")

##############################################################################################################

class LoadLevelerQueuesAgent(ComputingSharesAgent):
    def __init__(self, args={}):
        ComputingSharesAgent.__init__(self,args)
        self.name = "teragrid.glue2.LoadLevelerQueuesAgent"

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
        llclass = "llclass"
        try:
            llclass = self.config.get("loadleveler","llclass")
        except ConfigParser.Error:
            pass
        cmd = llclass + " -l"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("llclass failed: "+output)
            raise AgentError("llclass failed: "+output+"\n")

        queueStrings = []

        curIndex = 0
        nextIndex = output.find("=============== Class ",1)
        while nextIndex != -1:
            queueStrings.append(output[curIndex:nextIndex])
            curIndex = nextIndex
            nextIndex = output.find("=============== Class ",curIndex+1)
        queueStrings.append(output[curIndex:])

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

        queueName = None
	for line in lines:
            line = line.lstrip() # remove leading whitespace
            if line.find("Name:") >= 0:
                queueName = line[6:]
                break

        if queueName == None:
            print "didn't find queue name"
            sys.exit(1)

        ComputingShare.__init__(self,sensor)

        maxSlots = None
	for line in lines:
            line = line.lstrip() # remove leading whitespace
            if line.find("Name:") >= 0:
                queue.Name = line[6:]
                queue.MappingQueue = queue.Name
                queue.ID = "http://"+queue.sensor.getSystemName()+"/glue2/ComputingShare/"+queue.Name
            if line.find("Priority:") >= 0 and len(line) > 10:
                queue.Extension["Priority"] = int(line[10:])
            if line.find("Max_processors:") >= 0 and len(line) > 16:
                queue.MaxSlotsPerJob = int(line[16:])
                if queue.MaxSlotsPerJob == -1:
                    queue.MaxSlotsPerJob = None
            if line.find("Maxjobs:") >= 0 and len(line) > 9:
                queue.MaxTotalJobs = int(line[9:])
                if queue.MaxTotalJobs == -1:
                    queue.MaxTotalJobs = None
            if line.find("Class_comment:") >= 0:
                queue.Description = line[15:]
            if line.find("Wall_clock_limit:") >= 0 and len(line) > 18:
                (queue.MinWallTime,queue.MaxWallTime) = queue._getDurations(line[18:])
            if line.find("Cpu_limit:") >= 0 and len(line) > 11:
                (queue.MinCPUTime,queue.MaxCPUTime) = queue._getDurations(line[11:])
            if line.find("Job_cpu_limit:") >= 0 and len(line) > 15:
                (queue.MinTotalCPUTime,queue.MaxTotalCPUTime) = queue._getDurations(line[15:])
            if line.find("Free_slots:") >= 0 and len(line) > 12:
                queue.FreeSlots = int(line[12:])
                if maxSlots != None:
                    queue.UsedSlots = maxSlots - queue.FreeSlots
            if line.find("Maximum_slots:") >= 0 and len(line) > 15:
                maxSlots = int(line[15:])
                if queue.FreeSlots != None:
                    queue.UsedSlots = maxSlots - queue.FreeSlots

            # lets not include this right now in case of privacy concerns
            #if line.find("Include_Users:") >= 0 and len(line) > 15:
            #    queue.Extension["AuthorizedUsers"] = line[15:].rstrip()
            #if line.find("Exclude_Users:") >= 0 and len(line) > 15:
            #    queue.Extension["UnauthorizedUsers"] = line[15:].rstrip()
            #if line.find("Include_Groups:") >= 0 and len(line) > 16:
            #    queue.Extension["AuthorizedGroups"] = line[16:].rstrip()
            #if line.find("Exclude_Groups:") >= 0 and len(line) > 16:
            #    queue.Extension["UnauthorizedGroups"] = line[16:].rstrip()

            # no info on queue status?

        return queue

    def _getDurations(self, dStr):
        """Format is: Days+Hours:Minutes:Seconds, Days+Hours:Minutes:Seconds (XXX Seconds, XXX Seconds)
           in place of a duration, 'undefined' can be specified"""
        start = dStr.find("(")
        end = dStr.find(",",start)
        maxStr = dStr[start+1:end]

        maxDuration = None
        if maxStr != "undefined":
            maxDuration = int(maxStr[:len(maxStr)-8])

        start = end+2
        end = dStr.find(")",start)
        minStr = dStr[start:end]

        minDuration = None
        if minStr != "undefined":
            minDuration = int(minStr[:len(minStr)-8])

        return (minDuration,maxDuration)

##############################################################################################################

if __name__ == "__main__":
    agent = LoadLevelerQueuesAgent.createFromCommandLine()
    agent.runStdinStdout()
