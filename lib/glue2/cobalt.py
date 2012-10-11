
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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

from ipf.error import StepError

from glue2.log import LogDirectoryWatcher
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
        service.Name = "COBALT"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.Cobalt"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "Cobalt"
        manager.Name = "Cobalt"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):
    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("cqstat","the path to the Cobalt cqstat program (default 'cqstat')",False)

    def _run(self):
        cqstat = self.params.get("cqstat","cqstat")

        cmd = cqstat + " -lf"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("cqstat failed: "+output+"\n")

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
            if includeQueue(self.config,job.Queue):
                jobs.append(job)

        for job in jobs:
            job.id = job.LocalIDFromManager+"."+self._getSystemName()

        return jobs

    def _getJob(self, jobString):
        job = glue2.computing_activity.ComputingActivity()

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
                    job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
                elif state == "starting":
                    job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
                elif state == "running":
                    job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
                elif state.find("hold") != -1:
                    job.State = glue2.computing_activity.ComputingActivity.STATE_HELD
                elif state == "exiting":
                    job.State = glue2.computing_activity.ComputingActivity.STATE_FINISHED
                elif state == "killing":
                    job.State = glue2.computing_activity.ComputingActivity.STATE_TERMINATED
                else:
                    self.warning("found unknown Cobalt job state '" + state + "'")
                    job.State = glue2.computing_activity.ComputingActivity.STATE_UNKNOWN
            if line.startswith("    WallTime "):
                wallTime = self._getDuration(line.split()[2])
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
                    usedWallTime = self._getDuration(duration)
                    if job.RequestedSlots != None:
                        job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            #job.UsedTotalCPUTime = 
            if line.startswith("    SubmitTime "):
                job.ComputingManagerSubmissionTime = self._getSubmitDateTime(line[line.find(":")+2:])
            if line.startswith("    StartTime "):
                startTime = line[line.find(":")+2:]
                if startTime != "N/A":
                    job.StartTime = self._getStartDateTime(startTime)

            #job.ComputingManagerEndTime = job._getDateTime(line[line.find("=")+2:])

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

#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):

    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("cqstat","the path to the Cobalt cqstat program (default 'cqstat')",False)
        self._acceptParameter("cores_per_node",
                              "the number of processing cores per node is not provided by the Cobalt partlist program (default 8)",
                              False)

    def _run(self):

        cqstat = self.params.get("cqstat","cqstat")

        cmd = cqstat + " -lq"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("cqstat failed: "+output+"\n")

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
        queue = glue2.computing_share.ComputingShare()

        procs_per_node = self.prams.get("cores_per_node",8)

	lines = queueString.split("\n")
	for line in lines:
            if line.startswith("Name: "):
                queue.Name = line[6:]
                queue.MappingQueue = queue.Name
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
                    queue.MinWallTime = self._getDuration(minTime)
            if line.startswith("    MaxTime"):
                maxTime = line.split()[2]
                if maxTime != "None":
                    queue.MaxWallTime = self._getDuration(maxTime)
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
                    queue.Extension["MaxSlotsPerUser"] = int(maxUserNodes) * procs_per_node
            if line.startswith("    TotalNodes"):
                totalNodes = line.split()[2]
                if totalNodes != "None":
                    queue.Extension["MaxSlots"] = int(totalNodes) * procs_per_node
            if line.startswith("    Priority"):
                queue.Extension["Priority"] = float(line.split()[2])
        return queue

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):

    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("partlist","the path to the Cobalt partlist program (default 'partlist')",False)
        self._acceptParameter("cores_per_node",
                              "the number of processing cores per node is not provided by the Cobalt partlist program (default 8)",
                              False)
        self._acceptParameter("memory_per_node",
                              "the amount of memory per node (in MB) is not provided by the Cobalt partlist program (default 16384)",
                              False)

    def _run(self):
        partlist = self.params.get("partlist","partlist")

        cmd = partlist + " -a"
        selfr.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("partlist failed: "+output+"\n")

        lines = output.split("\n")

        avail_nodes = 0
        unavail_nodes = 0
        used_nodes = 0
        blocking = []
        smallest_partsize = -1
        largest_partsize = -1;
        for index in range(len(lines)-1,2,-1):
            #Name          Queue                             State                   Backfill
            #          1         2         3         4         5         6         7         8
            #012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
            toks = lines[index].split()
            toks2 = toks[0].split("_")

            partsize = int(toks2[0])

            if smallest_partsize == -1:
                smallest_partsize = partsize
            if partsize > largest_partsize:
                largest_partsize = partsize

            if partsize == smallest_partsize:
                toks2 = lines[index][48:].split()
                state = toks2[0]
                if state == "idle":
                    avail_nodes = avail_nodes + partsize
                elif state == "busy":
                    used_nodes = used_nodes + partsize
                elif state == "starting":
                    used_nodes = used_nodes + partsize
                elif state == "blocked":
                    if (lines[index].find("failed diags") != -1) or (lines[index].find("pending diags") != -1):
                        #blocked by pending diags
                        #failed diags
                        #blocked by failed diags
                        unavail_nodes = unavail_nodes + partsize
                    else:
                        blocked_by = toks2[1][1:len(toks2[1])-1]
                        if not blocked_by in blocking:
                            blocking.append(blocked_by)
                elif state == "hardware":
                    #hardware offline: nodecard <nodecard_id>
                    #hardware offline: switch <switch_id>
                    unavail_nodes = unavail_nodes + partsize
                else:
                    self.warning("found unknown partition state: "+toks[2])

        # assuming that all nodes are identical

        exec_env = glue2.execution_environment.ExecutionEnvironment()
        exec_env.LogicalCPUs = self.params.get("cores_per_node",8)
        exec_env.PhysicalCPUs = exec_env.LogicalCPUs

        exec_env.MainMemorySize = self.params.get("memory_per_node",16384)
        #exec_env.VirtualMemorySize = 

        # use the defaults set for Platform, OSVersion, etc in ExecutionEnvironment (same as the login node)

        exec_env.UsedInstances = used_nodes * exec_env.PhysicalCPUs
        exec_env.TotalInstances = (used_nodes + avail_nodes + unavail_nodes) * exec_env.PhysicalCPUs
        exec_env.UnavailableInstances = unavail_nodes * exec_env.PhysicalCPUs

        exec_env.Name = "NodeType1"

        return [exec_env]
        
#######################################################################################################################
