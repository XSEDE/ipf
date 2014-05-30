
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

from ipf.dt import *
from ipf.error import StepError

import glue2.computing_activity

##############################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self.requires.append(glue2.computing_activity.ComputingActivities)

        self._acceptParameter("showq","the path to the Moab showq program (default 'showq')",False)

        self.sched_name = "Moab"

    def _run(self):
        rm_jobs = {}
        for job in  self._getInput(glue2.computing_activity.ComputingActivities).activities:
            rm_jobs[job.LocalIDFromManager] = job

        moab_jobs = []
        try:
            self._addJobs("-c",moab_jobs) # get recently competed jobs - no big deal if it fails
        except StepError:
            pass
        self._addJobs("",moab_jobs)       # get the rest of the jobs

        # use jobs from Moab to order and correct jobs received from the resource manager
        for pos in range(0,len(moab_jobs)):
            moab_job = moab_jobs[pos]
            try:
                job = rm_jobs[moab_job.LocalIDFromManager]
                job.position = pos
                if job.State[0] != moab_job.State[0]:
                    job.State[0] = moab_job.State[0]
                job.State.append(moab_job.State[1])
            except KeyError:
                pass

        jobs = rm_jobs.values()
        jobs = sorted(jobs,key=self._jobPosition)
        jobs = sorted(jobs,key=self._jobStateKey)

        return jobs

    def _jobPosition(self, job):
        try:
            return job.position
        except AttributeError:
            self.warning("didn't find queue position for job %s in state %s" % (job.LocalIDFromManager,job.State))
            return sys.maxint


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
                    if self._includeQueue(job.Queue,True):
                        if job.EndTime == None:
                            jobs.append(job)
                        else:
                            # only provide info on the last 15 mins of completed jobs
                            if time.mktime(now.timetuple()) - time.mktime(job.EndTime.timetuple()) < 15 * 60:
                                jobs.append(job)
        doc.unlink()

    def _getJob(self, jobElement, procsPerNode, status):
        job = glue2.computing_activity.ComputingActivity()

        job.LocalIDFromManager = jobElement.getAttribute("JobID")
        job.Name = jobElement.getAttribute("JobName") # showing as NONE
        job.LocalOwner = jobElement.getAttribute("User")
        job.UserDomain = jobElement.getAttribute("Account")
        job.Queue = jobElement.getAttribute("Class")
        # using status is more accurate than using job State since Idle jobs can be blocked
        if status == "active":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
        elif status == "completed":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED]
        elif status == "eligible":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
        elif status == "blocked":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_HELD]
        else:
            logger.warn("found unknown Moab option '%s'",status)
            job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
        job.State.append("moab:"+status)

        epoch = float(jobElement.getAttribute("SubmissionTime"))
        job.SubmissionTime = datetime.datetime.fromtimestamp(epoch,localtzoffset())
        job.ComputingManagerSubmissionTime = job.SubmissionTime

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
