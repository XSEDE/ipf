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

from ipf.error import StepError
from glue2.log import LogDirectoryWatcher

from glue2.computing_activity import *

#######################################################################################################################

class LoadLevelerComputingActivitiesStep(ComputingActivitiesStep):

    def __init__(self, params):
        ComputingActivitiesStep.__init__(self,params)

        self.name = "glue2/loadleveler/computing_activities"
        self.accepts_params["llq"] = "the path to the Load Leveler llq program (default 'llq')"
        self.accepts_params["llstatus"] = "the path to the Load Leveler llstatus program (default 'llstatus')"

    def _run(self):
        self.info("running")

        llq = self.params.get("llq","llq")

        cmd = llq + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("llq failed: "+output+"\n")

        jobStrings = []

        curIndex = 0
        nextIndex = output.find("=============== Job Step ",1)
        while nextIndex != -1:
            jobStrings.append(output[curIndex:nextIndex])
            curIndex = nextIndex
            nextIndex = output.find("=============== Job Step ",curIndex+1)
        jobStrings.append(output[curIndex:])

        slotsPerNode = self._slotsPerNode()

        jobs = []
        for jobString in jobStrings:
            job = self._getJob(jobString,slotsPerNode)
            if includeQueue(job.Queue):
                jobs.append(job)

        for job in jobs:
            job.id = job.LocalIDFromManager+"."+self._getSystemName()

        return jobs

    def _slotsPerNode(self):

        llstatus = self.params.get("llstatus","llstatus")

        cmd = llstatus + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("llstatus failed: "+output)

	lines = output.split("\n")
        slotOccurances = {}
        for line in lines:
            if line.find("ConfiguredClasses") >= 0:
                minSlots = -1
                start = line.find("(")  # slot numbers are between ()
                end = line.find(")",start+1)
                while start != -1:
                    slots = int(line[start+1:end])
                    if minSlots < 0 or slots < minSlots:
                        minSlots = slots
                    start = line.find("(",end+1)
                    end = line.find(")",start+1)
                if minSlots != -1:
                    if slotOccurances.get(minSlots) == None:
                        slotOccurances[minSlots] = 1
                    else:
                        slotOccurances[minSlots] = slotOccurances[minSlots] + 1
        mostFrequentSlots = -1
        maxOccurances = -1
        for slots in slotOccurances.keys():
            if slotOccurances[slots] > maxOccurances:
               mostFrequentSlots = slots 
        return mostFrequentSlots

    def _getJob(self, jobString):
        job = ComputingActivity()

	lines = jobString.split("\n")

        requestedNodes = 1 # assume 1 node is requested if no info

        wallTime = None
        usedWallTime = None
	for line in lines:
            line = line.lstrip() # remove leading whitespace
            if line.find("Job Step Id:") >= 0:
                job.LocalIDFromManager = line[13:]
            if line.find("Job Name:") >= 0:
                job.Name = line[10:]
            if line.find("Owner:") >= 0:
                job.LocalOwner = line[7:]
            if line.find("Account:") >= 0:
                job.UserDomain = line[9:]
            if line.find("Class:") >= 0:
                job.Queue = line[7:]
            if line.find("Status:") >= 0:
                state = line[8:]
                if state == "Completed":
                    job.State = "teragrid:finished"
                elif state == "Canceled":
                    job.State = "teragrid:terminated"
                elif state == "Removed":
                    job.State = "teragrid:terminated"
                elif state == "Terminated":
                    job.State = "teragrid:terminated"
                elif state == "Remove Pending":
                    job.State = "teragrid:terminated"
                elif state == "Pending":
                    job.State = "teragrid:pending"
                elif state == "Idle":
                    job.State = "teragrid:pending"
                elif state == "Starting":
                    job.State = "teragrid:running"
                elif state == "Running":
                    job.State = "teragrid:running"
                elif state == "User Hold":
                    job.State = "teragrid:held"
                elif state == "Not Queued":
                    job.State = "teragrid:pending"
                else:
                    self.warn("found unknown LoadLeveler job state '" + state + "'")
                    job.State = "teragrid:unknown"
            if line.find("Wall Clk Hard Limit:") >= 0:
                wallTime = job._getDuration(line[21:])
            if line.find("Cpu Hard Limit:") >= 0:
                job.RequestedTotalCpuTime = job._getDuration(line[16:])

            # this isn't defined for some jobs
            if line.find("Node minimum") >= 0:
                requestedNodes = int(line[line.find(":")+2:])

            # don't see used CPU time anywhere
            #job.UsedTotalCPUTime = 

            if line.find("Queue Date:") >= 0 and len(line) > 12:
                job.ComputingManagerSubmissionTime = job._getDateTime(line[12:])
                job.SubmissionTime = job.ComputingManagerSubmissionTime

            if line.find("Dispatch Time:") >= 0 and len(line) > 15:
                job.StartTime = job._getDateTime(line[15:])
                usedWallTime = time.time() - time.mktime(job.StartTime.timetuple())

            if line.find("Completion Date:") >= 0 and len(line) > 17:
                job.ComputingManagerEndTime = job._getDateTime(line[17:])
                job.EndTime = job.ComputingManagerEndTime

        job.RequestedSlots = requestedNodes * slotsPerNode
        if wallTime != None:
            job.RequestedTotalWallTime = wallTime * job.RequestedSlots
        if usedWallTime != None:
            job.UsedTotalWallTime = usedWallTime * job.RequestedSlots

        return job

    def _getDuration(self, dStr):
        """Format is Days+Hours:Minutes:Seconds (XXX Seconds)"""
        start = dStr.find("(")
        end = dStr.find(" Seconds")
        if start >= 0 and end > start:
            return int(line[start:end])


    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # Example: Thu 04 Dec 2008 10:27:23 AM EST
        dayOfWeek = aStr[:3]
        day       = int(aStr[4:7])
        month     = aStr[7:10]
        year      = int(aStr[11:15])
        hour      = int(aStr[16:18])
        minute    = int(aStr[19:21])
        second    = int(aStr[22:24])
        ampm      = aStr[25:27]
        if ampm == "PM" and hour < 12:
            hour = hour + 12
        if ampm == "AM" and hour == 12:
            hour = 0
        # assume current time zone
        
        return datetime.datetime(year=year,
                                 month=self.monthDict[month],
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

#######################################################################################################################
