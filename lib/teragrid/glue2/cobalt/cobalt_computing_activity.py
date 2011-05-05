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
import xml.sax
import xml.sax.handler
import ConfigParser

from ipf.error import *
from teragrid.glue2.computing_activity import *

logger = logging.getLogger("CobaltJobsAgent")

##############################################################################################################

class CobaltJobsAgent(ComputingActivitiesAgent):
    def __init__(self, args={}):
        ComputingActivitiesAgent.__init__(self,args)
        self.name = "teragrid.glue2.CobaltJobsAgent"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        cqstat = "cqstat"
        try:
            cqstat = self.config.get("cobalt","cqstat")
        except ConfigParser.Error:
            pass

        cmd = qstat + " -lf"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("cqstat failed: "+output)
            raise AgentError("cqstat failed: "+output+"\n")

        jobStrings = []
        curIndex = output.find("JobID: ")
        if curIndex != -1:
            while True:
                nextIndex = output.find("JobID: ",curIndex+1)
                if nextIndex == -1:
                    jobStrings.append(output[curIndex:])
                    break
                else:
                    jobStrings.append(output[curIndex:nextIndex])
                    curIndex = nextIndex

        jobs = []
        for jobString in jobStrings:
            job = self._getJob(jobString)
            if includeQueue(job.Queue):
                jobs.append(job)

        for job in jobs:
            job.id = job.LocalIDFromManager+"."+self._getSystemName()

        return jobs

    def _getJob(self, jobString):
        job = ComputingActivity()

        # put multi-lines on one line
        #jobString.replace("\n\t","")

        wallTime = None
        usedWallTime = None
	lines = jobString.split("\n")
	for line in lines:
            if line.startswith("JobID: "):
                job.LocalIDFromManager = line[7:]
                job.ID = "http://"+self._getSystemName()+"/glue2/ComputingActivity/"+job.LocalIDFromManager
            if line.startswith("    JobName"):
                name = line.split()[2]
                if name != "-":
                    job.JobName = name
            if line.startswith("    User "):
                job.LocalOwner = line.split()[2]
            #if line.find("Account_Name =") >= 0:
            #    job.UserDomain = line.split()[2]
            if line.startswith("    Queue "):
                job.Queue = line.split()[2]
                job.ComputingShare = ["http://"+self._getSystemName()+"/glue2/ComputingShare/"+job.Queue]
            if line.startswith("    State "):
                state = line.split()[2]
                if state == "queued":
                    job.State = "teragrid:pending"
                elif state == "starting":
                    job.State = "teragrid:running"
                elif state == "running":
                    job.State = "teragrid:running"
                elif state.find("hold") != -1:
                    job.State = "teragrid:held"
                elif state == "exiting":
                    job.State = "teragrid:finished"
                elif state == "killing":
                    job.State = "teragrid:terminated"
                else:
                    logger.warn("found unknown Cobalt job state '" + state + "'")
                    job.State = "teragrid:unknown"
            if line.startswith("    WallTime "):
                wallTime = job._getDuration(line.split()[2])
                if job.RequestedSlots != None:
                    job.RequestedTotalWallTime = wallTime * job.RequestedSlots
            if line.startswith("    Nodes "):
                job.RequestedSlots = int(line.split()[2])
                if wallTime != None:
                    job.RequestedTotalWallTime = wallTime * job.RequestedSlots
                if usedWallTime != None:
                    job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            if line.startswith("    RunTime "):
                duration = line.split()[2]
                if duration != "N/A":
                    usedWallTime = job._getDuration(duration)
                    if job.RequestedSlots != None:
                        job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            #job.UsedTotalCPUTime = 
            if line.startswith("    SubmitTime "):
                job.ComputingManagerSubmissionTime = job._getSubmitDateTime(line[line.find(":")+2:])
                job.SubmissionTime = job.ComputingManagerSubmissionTime
            if line.startswith("    StartTime "):
                startTime = line[line.find(":")+2:]
                if startTime != "N/A":
                    job.StartTime = job._getStartDateTime(startTime)

            #job.ComputingManagerEndTime = job._getDateTime(line[line.find("=")+2:])
            #job.EndTime = job.ComputingManagerEndTime

        return job

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)


    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getSubmitDateTime(self, aStr):
        # Example: Fri May 30 06:54:25 2008
        # Not quite sure how it handles a different year... guessing
        dayOfWeek = aStr[:3]
        month     = aStr[4:7]
        day       = int(aStr[8:10])
        hour      = int(aStr[11:13])
        minute    = int(aStr[14:16])
        second    = int(aStr[17:19])
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

    def _getStartDateTime(self, aStr):
        # Example: 11/16/09 08:32:39
        month =  int(aStr[0:2])
        day =    int(aStr[3:5])
        year =   int(aStr[6:8])
        hour =   int(aStr[9:11])
        minute = int(aStr[12:14])
        second = int(aStr[15:17])

        # only works for dates after the year 2000
        return datetime.datetime(year=2000+year,
                                 month=month,
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

##############################################################################################################

if __name__ == "__main__":    
    agent = CobaltJobsAgent.createFromCommandLine()
    agent.runStdinStdout()
