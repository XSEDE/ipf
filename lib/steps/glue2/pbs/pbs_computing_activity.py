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
import datetime
import logging
import os
import re
import sys
import ConfigParser

from ipf.error import *
from teragrid.glue2.computing_activity import *

logger = logging.getLogger("PbsJobsAgent")

##############################################################################################################

class PbsJobsAgent(ComputingActivitiesAgent):
    def __init__(self, args={}):
        ComputingActivitiesAgent.__init__(self,args)
        self.name = "teragrid.glue2.PbsJobsAgent"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        qstat = "qstat"
        try:
            qstat = self.config.get("pbs","qstat")
        except ConfigParser.Error:
            pass

        cmd = qstat + " -f"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("qstat failed: "+output)
            raise AgentError("qstat failed: "+output+"\n")

        jobStrings = []
        curIndex = output.find("Job Id: ")
        if curIndex != -1:
            while True:
                nextIndex = output.find("Job Id: ",curIndex+1)
                if nextIndex == -1:
                    jobStrings.append(output[curIndex:])
                    break
                else:
                    jobStrings.append(output[curIndex:nextIndex])
                    curIndex = nextIndex

        jobs = []
        for jobString in jobStrings:
            job = self._getJob(jobString)
            if includeQueue(self.config,job.Queue):
                jobs.append(job)

        for job in jobs:
            job.id = job.LocalIDFromManager+"."+self._getSystemName()

        return jobs

    def _getJob(self, jobString):
        job = ComputingActivity()

        # put multi-lines on one line
        jobString.replace("\n\t","")

        wallTime = None
        usedWallTime = None
	lines = jobString.split("\n")
	for line in lines:
            if line.find("Job Id:") >= 0:
                job.LocalIDFromManager = line[8:]
                # remove the host name
                job.LocalIDFromManager = job.LocalIDFromManager.split(".")[0]
                job.ID = "http://"+self._getSystemName()+"/glue2/ComputingActivity/"+job.LocalIDFromManager
            if line.find("Job_Name =") >= 0:
                job.Name = line.split()[2]
            if line.find("Job_Owner =") >= 0:
                job.LocalOwner = line.split()[2].split("@")[0]
            if line.find("Account_Name =") >= 0:
                job.UserDomain = line.split()[2]
            if line.find("queue =") >= 0:
                job.Queue = line.split()[2]
            if line.find("job_state =") >= 0:
                state = line.split()[2]
                if state == "C":
                    # C is completing after having run
                    job.State = "teragrid:finished"
                elif state == "E":
                    # E is exiting after having run
                    job.State = "teragrid:terminated" #?
                elif state == "Q":
                    job.State = "teragrid:pending"
                elif state == "R":
                    job.State = "teragrid:running"
                elif state == "T":
                    job.State = "teragrid:pending"
                elif state == "Q":
                    job.State = "teragrid:pending"
                elif state == "S":
                    job.State = "teragrid:suspended"
                elif state == "H":
                    job.State = "teragrid:held"
                else:
                    logger.warn("found unknown PBS job state '" + state + "'")
                    job.State = "teragrid:unknown"
            if line.find("Resource_List.walltime =") >= 0:
                wallTime = self._getDuration(line.split()[2])
                if job.RequestedSlots != None:
                    job.RequestedTotalWallTime = wallTime * job.RequestedSlots
            # Just ncpus for some PBS installs. Both at other installs, with different values.
            if (line.find("Resource_List.ncpus =") >= 0) or (line.find("Resource_List.nodect =") >= 0):
                requestedSlots = int(line.split()[2])
                if (job.RequestedSlots == None) or (requestedSlots > job.RequestedSlots):
                    job.RequestedSlots = requestedSlots
                    if wallTime != None:
                        job.RequestedTotalWallTime = wallTime * job.RequestedSlots
                    if usedWallTime != None:
                        job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            if line.find("resources_used.walltime =") >= 0:
                usedWallTime = self._getDuration(line.split()[2])
                if job.RequestedSlots != None:
                    job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            if line.find("resources_used.cput =") >= 0:
                job.UsedTotalCPUTime = self._getDuration(line.split()[2])
            if line.find("qtime =") >= 0:
                job.ComputingManagerSubmissionTime = self._getDateTime(line[line.find("=")+2:])
            if line.find("mtime =") >= 0:
                if job.State == "teragrid:running":
                    job.StartTime = self._getDateTime(line[line.find("=")+2:])
                if (job.State == "teragrid:finished") or (job.State == "teragrid:terminated"):
                    # this is right for terminated since terminated is set on the E state
                    job.ComputingManagerEndTime = self._getDateTime(line[line.find("=")+2:])
            #if line.find("ctime =") >= 0 and \
            #        (job.State == "teragrid:finished" or job.State == "teragrid:terminated"):
            #    job.ComputingManagerEndTime = self._getDateTime(line[line.find("=")+2:])
            #    job.EndTime = job.ComputingManagerEndTime

        return job

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)


    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # Example: Fri May 30 06:54:25 2008
        # Not quite sure how it handles a different year... guessing
        dayOfWeek = aStr[:3]
        month =     aStr[4:7]
        day =       int(aStr[8:10])
        hour =      int(aStr[11:13])
        minute =    int(aStr[14:16])
        second =    int(aStr[17:19])
        if aStr[19] == ' ':
            year = int(aStr[20:24])
        else:
            year = datetime.datetime.today().year
        
        return datetime.datetime(year=year,
                                 month=self.monthDict[month],
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

##############################################################################################################

if __name__ == "__main__":    
    agent = PbsJobsAgent.createFromCommandLine()
    agent.runStdinStdout()
