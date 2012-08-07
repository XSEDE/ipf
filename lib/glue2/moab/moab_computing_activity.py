
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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
import os
import re
import sys
import xml.dom.minidom

from ipf.error import StepError
from glue2.log import LogDirectoryWatcher

from glue2.computing_activity import *

##############################################################################################################

class MoabComputingActivitiesStep(ComputingActivitiesStep):

    def __init__(self):
        ComputingActivitiesStep.__init__(self)

        self._acceptParameter("showq","the path to the Moab showq program (default 'showq')",False)

        self.sched_name = "Moab"

    def _run(self):
        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        jobs = []
        try:
            self._addJobs("-c",jobs) # get recently competed jobs - no big deal if it fails
        except AgentError:
            pass
        self._addJobs("",jobs)       # get the rest of the jobs
        return jobs

    def _addJobs(self, flag, jobs):
        try:
            showq = self.params["showq"]
        except KeyError:
            showq = "showq"

        cmd = showq + " "+flag+" --xml"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("showq failed: "+output+"\n")

        doc = xml.dom.minidom.parseString(output)

        now = datetime.datetime.now(localtzoffset())
        procsPerNode = 1.0
        for node in doc.firstChild.childNodes:
            if node.nodeName == "cluster":
                procsPerNode = float(node.getAttribute("LocalUpProcs")) / float(node.getAttribute("LocalUpNodes"))
                procsPerNode = round(procsPerNode,0)
            if node.nodeName == "queue":
                status = node.getAttribute("option")
                for jobElement in node.childNodes:
                    job = self._getJob(jobElement,procsPerNode,status)
                    if includeQueue(self.config,job.Queue):
                        if job.EndTime == None:
                            jobs.append(job)
                        else:
                            # only provide info on the last 15 mins of completed jobs
                            if time.mktime(now.timetuple()) - time.mktime(job.EndTime.timetuple()) < 15 * 60:
                                jobs.append(job)
        doc.unlink()

        return jobs

    def _getJob(self, jobElement, procsPerNode, status):
        job = ComputingActivity()

        job.LocalIDFromManager = jobElement.getAttribute("JobID")
        job.Name = jobElement.getAttribute("JobName") # showing as NONE
        job.LocalOwner = jobElement.getAttribute("User")
        job.UserDomain = jobElement.getAttribute("Account")
        job.Queue = jobElement.getAttribute("Class")
        if status == "active":
            job.State = ComputingActivity.STATE_RUNNING
        elif status == "completed":
            job.State = ComputingActivity.STATE_FINISHED
        elif status == "eligible":
            job.State = ComputingActivity.STATE_PENDING
        elif status == "blocked":
            job.State = ComputingActivity.STATE_HELD
        else:
            logger.warn("found unknown Moab option '%s'",status)
            job.State = ComputingActivity.STATE_UNKNOWN

        epoch = float(jobElement.getAttribute("SubmissionTime"))
        job.ComputingManagerSubmissionTime = datetime.datetime.fromtimestamp(epoch,localtzoffset())

        epoch = jobElement.getAttribute("StartTime")
        if (epoch != "") and (epoch != "0"):
            job.StartTime = datetime.datetime.fromtimestamp(float(epoch),localtzoffset())
 
        job.RequestedSlots = int(jobElement.getAttribute("ReqProcs"))

        epoch = jobElement.getAttribute("CompletionTime")
        if (epoch != "") and (epoch != "0"):
            job.ComputingManagerEndTime = datetime.datetime.fromtimestamp(float(epoch),localtzoffset())

        wallTime = jobElement.getAttribute("ReqAWDuration")
        if wallTime != "":
            job.RequestedTotalWallTime = int(wallTime) * job.RequestedSlots
        usedWallTime = jobElement.getAttribute("AWDuration")
        if usedWallTime != "":
            job.UsedTotalWallTime = int(usedWallTime) * job.RequestedSlots

        exitCode = jobElement.getAttribute("CompletionCode")
        if exitCode != "":
            job.ExitCode = exitCode

        # don't see used CPU time anywhere
        #job.UsedTotalCPUTime = 

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

##############################################################################################################

# don't see a Moab log file with job information, so no update class.
