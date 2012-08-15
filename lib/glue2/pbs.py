
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
import re

from ipf.error import StepError

import glue2.computing_activity
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
from glue2.log import LogDirectoryWatcher
from glue2.execution_environment import *
from glue2.teragrid.platform import PlatformMixIn

#######################################################################################################################

class ComputingServiceStep(glue2.computing_service.ComputingServiceStep):

    def __init__(self):
        glue2.computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = glue2.computing_service.ComputingService()
        service.Name = "PBS"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.PBS"
        service.QualityLevel = "production"

        return service
        
#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "PBS"
        manager.Name = "PBS"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("qstat","the path to the PBS qstat program (default 'qstat')",False)

    def _run(self):
        qstat = self.params.get("qstat","qstat")

        # what flavors is -x (xml) available in?
        cmd = qstat + " -f"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("qstat failed: "+output+"\n")

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
            if self._includeQueue(job.Queue):
                jobs.append(job)

        return jobs

    def _getJob(self, jobString):
        job = glue2.computing_activity.ComputingActivity()

        # put multi-lines on one line
        jobString = jobString.replace("\n\t","")

        m = re.search("Job Id: (\S+)",jobString)
        if m is not None:
            # remove the host name
            job.LocalIDFromManager = m.group(1).split(".")[0]
        m = re.search("Job_Name = (\S+)",jobString)
        if m is not None:
            job.Name = m.group(1)
        m = re.search("Job_Owner = (\S+)",jobString)
        if m is not None:
            # remove the host name
            job.LocalOwner = m.group(1).split("@")[0]
        m = re.search("Account_Name = (\S+)",jobString)
        if m is not None:
            job.UserDomain = m.group(1)
        m = re.search("queue = (\S+)",jobString)
        if m is not None:
            job.Queue = m.group(1)
        m = re.search("job_state = (\S+)",jobString)
        if m is not None:
            state = m.group(1)
            if state == "C":
                # C is completing after having run
                job.State = glue2.computing_activity.ComputingActivity.STATE_FINISHED
            elif state == "E":
                # E is exiting after having run
                job.State = glue2.computing_activity.ComputingActivity.STATE_TERMINATED #?
            elif state == "Q":
                job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            elif state == "R":
                job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            elif state == "T":
                job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            elif state == "Q":
                job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            elif state == "S":
                job.State = glue2.computing_activity.ComputingActivity.STATE_SUSPENDED
            elif state == "H":
                job.State = glue2.computing_activity.ComputingActivity.STATE_HELD
            else:
                self.warning("found unknown PBS job state '%s'",state)
                job.State = glue2.computing_activity.ComputingActivity.STATE_UNKNOWN
        # Just ncpus for some PBS installs. Both at other installs, with different values.
        m = re.search("Resource_List.ncpus = (\d+)",jobString)
        if m is not None:
            cpus = int(m.group(1))
        else:
            cpus = None
        m = re.search("Resource_List.nodect = (\d+)",jobString)
        if m is not None:
            job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.nodes = (\d+)",jobString)
        if m is not None:
            requested_slots = int(m.group(1))
            if job.RequestedSlots is None or requested_slots > job.RequestedSlots:
                job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.nodes = (\d+):ppn=(\d+)",jobString)
        if m is not None:
            job.RequestedSlots = int(m.group(1)) * int(m.group(2))
        m = re.search("Resource_List.walltime = (\S+)",jobString)
        if m is not None:
            wall_time = self._getDuration(m.group(1))
            if job.RequestedSlots is not None:
                job.RequestedTotalWallTime = wall_time * job.RequestedSlots
        m = re.search("resource_used.walltime = (\S+)",jobString)
        if m is not None:
            used_wall_time = self._getDuration(m.group(1))
            if job.RequestedSlots is not None:
                job.UsedTotalWallTime = used_wall_time * job.RequestedSlots
        m = re.search("resource_used.cput = (\S+)",jobString)
        if m is not None:
            job.UsedTotalCPUTime = self._getDuration(m.group(1))
        m = re.search("qtime.cput = (\S+)",jobString)
        if m is not None:
            job.ComputingManagerSubmissionTime = self._getDateTime(m.group(1))
        m = re.search("mtime = (\w+ \w+ \d+ \d+:\d+:\d+ \d+)",jobString)
        if m is not None:
            if job.State == glue2.computing_activity.ComputingActivity.STATE_RUNNING:
                job.StartTime = self._getDateTime(m.group(1))
            if (job.State == glue2.computing_activity.ComputingActivity.STATE_FINISHED) or \
                   (job.State == glue2.computing_activity.ComputingActivity.STATE_TERMINATED):
                # this is right for terminated since terminated is set on the E state
                job.ComputingManagerEndTime = self._getDateTime(m.group(1))

        m = re.search("exec_host = (\S+)",jobString)
        if m is not None:
            # exec_host = c013.cm.cluster/7+c013.cm.cluster/6+...
            nodes = set(map(lambda s: s.split("/")[0], m.group(1).split("+")))
            job.ExecutionNode = list(nodes)

        #m = re.search("ctime = (\S+)",jobString)
        #if m is not None:
        #    if line.find("ctime =") >= 0 and \
        #           (job.State == ComputingActivity.STATE_FINISHED or job.State == ComputingActivity.STATE_TERMINATED):
        #        job.ComputingManagerEndTime = self._getDateTime(m.group(1))
        #        job.EndTime = job.ComputingManagerEndTime

        return job

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)


    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, dt_str):
        # Example: Fri May 30 06:54:25 2008
        # Not quite sure how it handles a different year... guessing

        m = re.search("(\w+) (\w+) (\d+) (\d+):(\d+):(\d+) (\d+)",dt_str)
        if m is None:
            raise StepError("can't parse '%s' as a date/time" % dt_str)
        dayOfWeek = m.group(1)
        month =     self.monthDict[m.group(2)]
        day =       int(m.group(3))
        hour =      int(m.group(4))
        minute =    int(m.group(5))
        second =    int(m.group(6))
        year =      int(m.group(7))
        
        return datetime.datetime(year=year,
                                 month=month,
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

#######################################################################################################################

class ComputingActivityUpdateStep(glue2.computing_activity.ComputingActivityUpdateStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivityUpdateStep.__init__(self)

        self._acceptParameter("server_logs_dir","the path to the PBS spool/server_logs directory (optional)",False)

        # caching job information may not be the best idea for systems with very large queues...
        self.activities = {}

        self.nodes = {}    # save a list of nodes allocated to a job

    def _run(self):
        try:
            dir_name = self.params["server_logs_dir"]
        except KeyError:
            try:
                dir_name = os.path.join(os.environ["PBS_HOME"],"spool","server_logs")
            except KeyError:
                raise StepError("server_logs_dir not specified and the PBS_HOME environment variable is not set")

        watcher = LogDirectoryWatcher(self._logEntry,dir_name)
        watcher.run()

    def _logEntry(self, log_file_name, entry):
        # log time
        # entry type
        # source (PBS_Server, ...)
        # Svr/Req/Job
        # ? job id (with Job)
        # message
        toks = entry.split(";")
        if len(toks) < 6:
            self.warning("too few tokens in line: %s",entry)
            return
        type = toks[1]
        if type == "0002":
            # batch system/server events
            if toks[5] == "Log closed":
                # move on to the next log
                return False
        elif type == "0008":
            # job events
            self._handleJobEntry(toks)
        elif type == "0010":
            # job resource usage
            pass
        elif type == "0040":
            # server sending requests (including allocation)
            self._handleRequest(toks)
        else:
            #self.debug("unknown type %s",type)
            pass
        return True

    def _handleRequest(self, toks):
        if toks[4] != "set_nodes":
            return
        m = re.search("job (\S+) ",toks[5])
        if m is None:
            return
        id = m.group(1).split(".")[0]  # just the id part of id.host.name

        m = re.search(" \(nodelist=([^\)]+)\)",toks[5])
        if m is None:
            return
        self.nodes[id] = list(set(map(lambda s: s.split("/")[0], m.group(1).split("+"))))
            
    def _handleJobEntry(self, toks):
        id = toks[4].split(".")[0]  # just the id part of id.host.name
        try:
            activity = self.activities[id]
        except KeyError:
            activity = glue2.computing_activity.ComputingActivity()
            activity.LocalIDFromManager = id
            self.activities[id] = activity
        if "Job Queued" in toks[5]:
            activity.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            activity.ComputingManagerSubmissionTime = self._getDateTime(toks[0])
            try:
                m = re.search(" owner = (\w+)@(\S*),",toks[5])  # just the user part of user@host
                activity.LocalOwner = m.group(1)
            except AttributeError:
                self.warning("didn't find owner in log mesage: %s",toks)
                return
            try:
                m = re.search(" job name = (\S+)",toks[5])
                #activity.Name = m.group(1).split(".")[0]  # just the a part of a.b.?
                activity.Name = m.group(1)
            except AttributeError:
                self.warning("didn't find job name in log mesage: %s",toks)
                return
            try:
                m = re.search(" queue = (\S+)",toks[5])
                activity.Queue = m.group(1).split(".")[0]
            except AttributeError:
                self.warning("didn't find queue in log mesage: %s",toks)
                return
        elif "Job Run" in toks[5]:
            activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            activity.StartTime = self._getDateTime(toks[0])
            try:
                activity.ExecutionNode = self.nodes[activity.LocalIDFromManager]
                del self.nodes[activity.LocalIDFromManager]
            except KeyError:
                pass
        elif "Job deleted" in toks[5]:
            activity.State = glue2.computing_activity.ComputingActivity.STATE_TERMINATED
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "JOB_SUBSTATE_EXITING" in toks[5]:
            activity.State = glue2.computing_activity.ComputingActivity.STATE_FINISHED
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "Job sent signal SIGKILL on delete" in toks[5]:
            # job ran too long and was killed
            activity.State = Cglue2.computing_activity.omputingActivity.STATE_TERMINATED
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "Job Modified" in toks[5]:
            # when nodes aren't available, log has jobs that quickly go from Job Queued to Job Run to Job Modified
            # and the jobs are pending after this
            if activity.State == glue2.computing_activity.ComputingActivity.STATE_RUNNING:
                activity.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
                activity.StartTime = None
            else:
                self.warning("not sure how to handle log event: %s",toks)
        else:
            self.warning("unhandled log event: %s",toks)
            return

        if activity.Queue is None or self._includeQueue(activity.Queue):
            self.output(activity)
            

    def _getDateTime(self, dt_str):
        # Example: 06/10/2012 16:17:41
        m = re.search("(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)",dt_str)
        if m is None:
            raise StepError("can't parse '%s' as a date/time" % dt_str)
        month = int(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        second = int(m.group(6))
        return datetime.datetime(year=year,
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

        self._acceptParameter("qstat","the path to the PBS qstat program (default 'qstat')",False)

    def _run(self):
        qstat = self.params.get("qstat","qstat")
        cmd = qstat + " -q -G"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qstat failed: "+output)
            raise StepError("qstat failed: "+output+"\n")

        queueStrings = output.split("\n")
        queueStrings = queueStrings[5:len(queueStrings)-2]

        queues = []
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if self._includeQueue(queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = glue2.computing_share.ComputingShare()

        (queueName,
         memoryLimitGB,
         cpuTimeLimit,
         wallTimeLimit,
         nodeLimit,
         runningJobs,
         queuedJobs,
         maxRunningJobs,
         enableDisable,
         runningStopped) = queueString.split()

        queue.Name = queueName
        queue.MappingQueue = queue.Name
        if cpuTimeLimit != "--":
            queue.MaxTotalCPUTime = self._getDuration(cpuTimeLimit)
        if wallTimeLimit != "--":
            queue.MaxWallTime = self._getDuration(wallTimeLimit)
        if nodeLimit != "--":
            queue.MaxSlotsPerJob = int(nodeLimit)
        queue.TotalJobs = 0
        if runningJobs != "--":
            queue.LocalRunningJobs = int(runningJobs)
            queue.RunningJobs = queue.LocalRunningJobs
            queue.TotalJobs = queue.TotalJobs + queue.RunningJobs
        if queuedJobs != "--":
            queue.LocalWaitingJobs = int(queuedJobs)
            queue.WaitingJobs = queue.LocalWaitingJobs
            queue.TotalJobs = queue.TotalJobs + queue.WaitingJobs
        if maxRunningJobs != "--":
            queue.MaxRunningJobs = int(maxRunningJobs)
        if enableDisable == "E":
            queue.Extension["AcceptingJobs"] = True
        else:
            queue.Extension["AcceptingJobs"] = False
        if runningStopped == "R":
            queue.Extension["RunningJobs"] = True
        else:
            queue.Extension["RunningJobs"] = False

        return queue


    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):
    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("pbsnodes","the path to the PBS pbsnodes program (default 'pbsnodes')",False)
        self._acceptParameter("nodes",
                              "An expression describing the nodes to include (optional). The syntax is a series of +<property> and -<property> where <property> is the name of a node property or a '*'. '+' means include '-' means exclude. The expression is processed in order and the value for a node at the end determines if it is shown.",
                              False)

    def _run(self):
        pbsnodes = self.params.get("pbsnodes","pbsnodes")

        cmd = pbsnodes + " -a"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("pbsnodes failed: "+output)
            raise StepError("pbsnodes failed: "+output+"\n")

        nodeStrings = output.split("\n\n")
        hosts = map(self._getHost,nodeStrings)
        hosts = filter(self._testProperties,hosts)
        hosts = filter(self._goodHost,hosts)
        return hosts

    def _getHost(self, nodeString):
        host = glue2.execution_environment.ExecutionEnvironment()

        host.properties = ()

        lines = nodeString.split("\n")

        # ID set by ExecutionEnvironment
        host.Name = lines[0]
        various = False
        for line in lines[1:]:
            if line.find("state =") >= 0:
                if line.find("free") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                elif line.find("offline") >= 0 or line.find("down") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 1
                elif line.find("job-exclusive") or line.find("job-busy") >= 0:
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif line.find("<various>") >= 0:
                    various = True
                host.TotalInstances = 1
            if various and line.find("resources_assigned.ncpus =") >= 0:
                # when state is <various>, figure out used based on assigned cpus
                host.UnavailableInstances = 0
                host.UsedInstances = 0
                if host.PhysicalCPUs != None:
                    assignedCpus = int(line.split()[2])
                    if assignedCpus == host.PhysicalCPUs:
                        host.UsedInstances = 1
            if line.find("np =") >= 0 or line.find("resources_available.ncpus =") >= 0:
                cpus = int(line.split()[2])
                if (host.PhysicalCPUs == None) or (cpus > host.PhysicalCPUs):
                    host.PhysicalCPUs = cpus
                    host.LogicalCPUs = host.PhysicalCPUs        # don't have enough info to do anything else...
            if line.find("resources_available.mem =") >= 0:
                memSize = line.split("=")[1]
                host.MainMemorySize = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
            if line.find("resources_available.vmem =") >= 0:
                memSize = line.split("=")[1]
                host.VirtualMemorySize = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
            if line.find("status =") >= 0:
                toks = line[14:].split(",")
                for tok in toks:
                    if tok.find("totmem=") >= 0:
                        memSize = tok.split("=")[1]
                        totMem = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
                    if tok.find("physmem=") >= 0:
                        memSize = tok.split("=")[1]
                        host.MainMemorySize = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
                    if tok.find("opsys=") >= 0:
                        if tok.split("=")[1] == "linux":
                            host.OSFamily = "linux"
                    if tok.find("uname=") >= 0:
                        utoks = tok.split()
                        host.Platform = utoks[len(utoks)-1]
			host.OSVersion = utoks[2]
                    if tok.find("ncpus=") >= 0:
                        cpus = int(tok.split("=")[1])
                        if (host.PhysicalCPUs == None) or (cpus > host.PhysicalCPUs):
                            host.PhysicalCPUs = cpus
                            host.LogicalCPUs = host.PhysicalCPUs        # don't have enough info to do anything else...
                    if tok.find("loadave=") >= 0:
                        load = float(tok.split("=")[1])
                        if host.UsedInstances > 0:
                            host.Extension["UsedAverageLoad"] = load
                        elif host.UnavailableInstances == 0:
                            host.Extension["UsedAvailableLoad"] = load
                host.VirtualMemorySize = totMem - host.MainMemorySize
            if line.find("properties =") >= 0:
                host.properties = line[18:].split(",")
        return host
        
    def _testProperties(self, host):
        nodes = self.params.get("nodes","+*")
        toks = nodes.split()
        goodSoFar = False
        for tok in toks:
            if tok[0] == '+':
                prop = tok[1:]
                if (prop == "*") or (prop in host.properties):
                    goodSoFar = True
            elif tok[0] == '-':
                prop = tok[1:]
                if (prop == "*") or (prop in host.properties):
                    goodSoFar = False
            else:
                self.warn("can't parse part of nodes expression: "+tok)
        return goodSoFar

#######################################################################################################################

class TeraGridExecutionEnvironmentsStep(ExecutionEnvironmentsStep, PlatformMixIn):
    def __init__(self):
        ExecutionEnvironmentsStep.__init__(self)
        PlatformMixIn.__init__(self)

    def _run(self):
        hosts = ExecutionEnvironmentsStep._run(self)
        self.addTeraGridPlatform(hosts)
        return hosts

#######################################################################################################################
