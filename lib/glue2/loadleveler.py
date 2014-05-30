
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

from ipf.error import StepError
from ipf.log import LogDirectoryWatcher

import glue2.computing_activity
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
import glue2.execution_environment

#######################################################################################################################

class ComputingServiceStep(glue2.computing_service.ComputingServiceStep):

    def __init__(self):
        glue2.computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = glue2.computing_service.ComputingService()
        service.Name = "LoadLeveler"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.LoadLeveler"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "LoadLeveler"
        manager.Name = "LoadLeveler"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("llq","the path to the Load Leveler llq program (default 'llq')",False)
        self._acceptParameter("llstatus","the path to the Load Leveler llstatus program (default 'llstatus')",False)

    def _run(self):
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
        job = glue2.computing_activity.ComputingActivity()

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
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED]
                elif state == "Canceled":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
                elif state == "Removed":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
                elif state == "Terminated":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
                elif state == "Remove Pending":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
                elif state == "Pending":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
                elif state == "Idle":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
                elif state == "Starting":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
                elif state == "Running":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
                elif state == "User Hold":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_HELD]
                elif state == "Not Queued":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
                else:
                    self.warn("found unknown LoadLeveler job state '" + state + "'")
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
                job.State.append("loadleveler:"+state.replace(" ",""))
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

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):
    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("llclass","the path to the Load Leveler llclass program (default 'llclass')",False)

    def _run(self):
        llclass = self.params.get("llclass","llclass")

        cmd = llclass + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("llclass failed: "+output+"\n")

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
        queue = glue2.computing_share.ComputingShare()

	lines = queueString.split("\n")

        queueName = None
	for line in lines:
            line = line.lstrip() # remove leading whitespace
            if line.find("Name:") >= 0:
                queueName = line[6:]
                break

        if queueName == None:
            raise StepError("didn't find queue name")

        maxSlots = None
	for line in lines:
            line = line.lstrip() # remove leading whitespace
            if line.find("Name:") >= 0:
                queue.Name = line[6:]
                queue.MappingQueue = queue.Name
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
                (queue.MinWallTime,queue.MaxWallTime) = self._getDurations(line[18:])
            if line.find("Cpu_limit:") >= 0 and len(line) > 11:
                (queue.MinCPUTime,queue.MaxCPUTime) = self._getDurations(line[11:])
            if line.find("Job_cpu_limit:") >= 0 and len(line) > 15:
                (queue.MinTotalCPUTime,queue.MaxTotalCPUTime) = self._getDurations(line[15:])
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
        if start == -1:
            # no (..., ...) so must be unknown
            return (None,None)
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

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):

    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("llstatus","the path to the Load Leveler llstatus program (default 'llstatus')",False)

    def _run(self):
        llstatus = self.params.get("llstatus","llstatus")

        cmd = llstatus + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("llstatus failed: "+output+"\n")

        nodeStrings = []

        curIndex = 0
        nextIndex = output.find("===============================================================================",1)
        while nextIndex != -1:
            nodeStrings.append(output[curIndex:nextIndex])
            curIndex = nextIndex
            nextIndex = output.find("===============================================================================",
                                    curIndex+1)
        nodeStrings.append(output[curIndex:])

        hosts = []
        for nodeString in nodeStrings:
            host = self._getHost(nodeString)
            if self._goodHost(host):
                hosts.append(host)

        return self._groupHosts(hosts)

    def _getHost(self, nodeString):
        host = glue2.execution_environment.ExecutionEnvironment()

        lines = nodeString.split("\n")

        load = None
        # ID set by ExecutionEnvironment
        for line in lines[1:]:
            if line.startswith("Name "):
                host.Name = line[line.find("=")+2:]
            if line.startswith("LoadAvg "):
                load = float(line[line.find("=")+2:])
            if line.startswith("State "):
                host.TotalInstances = 1
                if line.find("Busy") >= 0:
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif line.find("Running") >= 0: # ?
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif line.find("Idle") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                elif line.find("Down") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 1
                elif line.find("None") >= 0: # central manager seems to have a state of None
                    host.TotalInstances = 0 # don't include this host
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                else: # guess starting and stopping
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                host.TotalInstances = 1
                if load != None:
                    if host.UsedInstances > 0:
                        host.Extension["UsedAverageLoad"] = load
                    elif host.UnavailableInstances == 0:
                        host.Extension["AvailableAverageLoad"] = load
            # Not sure of the best way to get LogicalCPUs. I'm using it to calculate slots, so probably 2nd way
            if line.startswith("Cpus "):
                host.PhysicalCPUs = int(line[line.find("=")+2:])
                #host.LogicalCPUs = host.PhysicalCPUs
            if line.startswith("Max_Starters "):
                host.LogicalCPUs = int(line[line.find("=")+2:])
            if line.startswith("OpSys "):
                if line.find("Linux"):
                    host.OSFamily = "linux"
            if line.startswith("Arch "):
                host.Platform = line[line.find("=")+2:]
            if line.startswith("Memory "):
                host.MainMemorySize = self._getMB(line[line.find("=")+2:].split())
            if line.startswith("VirtualMemory "):
                host.VirtualMemorySize = self._getMB(line[line.find("=")+2:].split())
        return host

    def _getMB(self, namevalue):
        (value,units) = namevalue
        if units == "kb":
            return int(value) / 1024
        if units == "mb":
            return int(value)
        if units == "gb":
            return int(value) * 1024
        
#######################################################################################################################
