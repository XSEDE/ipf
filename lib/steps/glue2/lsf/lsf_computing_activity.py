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

class LsfComputingActivitiesStep(ComputingActivitiesStep):

    def __init__(self, params):
        ComputingActivitiesStep.__init__(self,params)

        self.name = "glue2/lsf/computing_activities"
        self.accepts_params["bjobs"] = "the path to the LSF bjobs program (default 'bjobs')"

    def _run(self):
        self.info("running")

        bjobs = self.params.get("bjobs","bjobs")

        cmd = bjobs + " -a -l -u all"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("bjobs failed: "+output+"\n")

        jobStrings = output.split("------------------------------------------------------------------------------")
        for jobString in jobStrings:
            job = self._getJob(jobString)
            if includeQueue(job.Queue):
                self.activities.append(job)

        return jobList

    def _getJob(self, jobString):
        job = ComputingActivity()

        # put records that are multiline on one line
        jobString = re.sub("\n                     ","",jobString)

        jobString = re.sub("\r","\n",jobString)
        lines = []
        for line in jobString.split("\n"):
            if len(line) > 0:
                lines.append(line)

        # line 0 has job information
        m = re.search(r"Job\s*<\S*>",lines[0])
        if m != None:
            job.LocalIDFromManager = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find Job")
        m = re.search(r"Job Name\s*<\S*>",lines[0])
        if m != None:
            job.Name = job._betweenAngleBrackets(m.group())
        else:
            self.info("didn't find Job Name")
                
        m = re.search(r"User\s*<\S*>",lines[0])
        if m != None:
            job.LocalOwner = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find User")
            job.LocalOwner = "UNKNOWN"

        m = re.search(r"Project\s*<\S*>",lines[0])
        if m != None:
            job.UserDomain = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find Project")

        m = re.search(r"Queue\s*<\S*>",lines[0])
        if m != None:
            job.Queue = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find Queue in "+lines[0])

        m = re.search(r"Status\s*<\S*>",lines[0])
        currentState = None
        if m != None:
            tempStr = m.group()
            status = job._betweenAngleBrackets(tempStr)
            if status == "RUN":
                job.State = "teragrid:running"
            elif status == "PEND":
                job.State = "teragrid:pending"
            elif status == "PSUSP": # job suspended by user while pending
                # ComputingShare has SuspendedJobs, so there should be a suspended state here
                job.State = "teragrid:held"
            elif status == "USUSP":
                job.State = "teragrid:suspended"
            elif status == "DONE":
                job.State = "teragrid:finished"
            elif status == "ZOMBI":
                job.State = "teragrid:terminated"
            elif status == "EXIT":
                job.State = "teragrid:terminated"
            elif status == "UNKWN":
                job.State = "teragrid:unknown"
            else:
                self.warn("found unknown status '"+status+"'")
                job.State = "teragrid:unknown"
        else:
            self.warn("didn't find Status in "+lines[0])
            job.State = "teragrid:unknown"

        #m = re.search(r"Command <\S*>",lines[0])
        #tempStr = m.group()
        #tempStr[9:len(tempStr)-1]

        # lines[1] has the submit time

        #submitTime = job._getDateTime(lines[1])

        #job.addStateChange(JobStateChange(WaitingJobState(),submitTime))

        # lines[1] also has the requested processors

        m = re.search(r"\d+ Processors Requested",lines[1])
        if m != None:
            tempStr = m.group()
            job.RequestedSlots = int(tempStr.split()[0])
        else:
            self.info("didn't find Processors, assuming 1")
            job.RequestedSlots = 1

        # run limit should be in lines[3], but had one case where it wasn't
        for lineNum in range(0,len(lines)):
            if lines[lineNum].find("RUNLIMIT") != -1:
                minPos = lines[lineNum+1].find("min")
                runLimitStr = lines[lineNum+1][1:minPos-1]
                wallTime = int(float(runLimitStr)) * 60
                job.RequestedTotalWallTime = wallTime * job.RequestedSlots

        # lines[6] has the start time in it, if any

        # check the lines for events and any pending reason
        for index in range(0,len(lines)):
            if lines[index].find("Submitted from") != -1:
                job.ComputingManagerSubmissionTime = job._getDateTime(lines[index])
            elif lines[index].find("Started on") != -1:
                job.StartTime = job._getDateTime(lines[index])
                usedWallTime = time.time() - time.mktime(job.StartTime.timetuple())
                job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            elif lines[index].find("Done successfully") != -1:
                job.ComputingManagerEndTime = job._getDateTime(lines[index])
            elif lines[index].find("Exited with exit code 1") != -1:
                job.ComputingManagerEndTime = job._getDateTime(lines[index])
            if lines[index].find("PENDING REASONS:") != -1:
                if lines[index+1].find("Job's resource requirements not satisfied") != -1:
                    # teragrid:pending is correct
                    pass
                elif lines[index+1].find("New job is waiting for scheduling") != -1:
                    # teragrid:held is probably better
                    job.State = "teragrid:held"
                else:
                    # teragrid:held is better, even though LSF calls it PEND. some examples:
                    # Job dependency condition not satisfied;
                    self.info("setting state to held for pending reason: "+lines[index+1])
                    job.State = "teragrid:held"

        return job

    def _betweenAngleBrackets(self, aStr):
        leftPos = aStr.find("<")
        rightPos = aStr.find(">")
        return aStr[leftPos+1:rightPos]

    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # Example: Mon May 14 14:24:11:
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

#######################################################################################################################
