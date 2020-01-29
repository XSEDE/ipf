
###############################################################################
#   Copyright 2012-2014 The University of Texas at Austin                     #
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

import subprocess
import datetime
import os
import re

from ipf.dt import localtzoffset
from ipf.error import StepError
from ipf.log import LogDirectoryWatcher

from . import computing_activity
from . import computing_manager
from . import computing_service
from . import computing_share
from . import execution_environment
from . import accelerator_environment
from . import computing_manager_accel_info
from . import computing_share_accel_info

#######################################################################################################################


class ComputingServiceStep(computing_service.ComputingServiceStep):

    def __init__(self):
        computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = computing_service.ComputingService()
        service.Name = "PBS"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "ipf.PBS"
        service.QualityLevel = "production"

        return service

#######################################################################################################################


class ComputingManagerStep(computing_manager.ComputingManagerStep):

    def __init__(self):
        computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = computing_manager.ComputingManager()
        manager.ProductName = "PBS"
        manager.Name = "PBS"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################


class ComputingActivitiesStep(computing_activity.ComputingActivitiesStep):

    def __init__(self):
        computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter(
            "qstat", "the path to the PBS qstat program (default 'qstat')", False)

    def _run(self):
        qstat = self.params.get("qstat", "qstat")

        # what flavors is -x (xml) available in?
        cmd = qstat + " -f"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("qstat failed: "+output+"\n")

        jobStrings = []
        curIndex = output.find("Job Id: ")
        if curIndex != -1:
            while True:
                nextIndex = output.find("Job Id: ", curIndex+1)
                if nextIndex == -1:
                    jobStrings.append(output[curIndex:])
                    break
                else:
                    jobStrings.append(output[curIndex:nextIndex])
                    curIndex = nextIndex

        jobs = []
        for jobString in jobStrings:
            job = self._getJob(jobString, self)
            if self._includeQueue(job.Queue):
                jobs.append(job)

        return jobs

    @classmethod
    def _getJob(cls, jobString, step):
        job = computing_activity.ComputingActivity()

        # put multi-lines on one line
        jobString = jobString.replace("\n\t", "")

        m = re.search("Job Id: (\S+)", jobString)
        if m is not None:
            # remove the host name
            job.LocalIDFromManager = m.group(1).split(".")[0]
        m = re.search("Job_Name = (\S+)", jobString)
        if m is not None:
            job.Name = m.group(1)
        m = re.search("Job_Owner = (\S+)", jobString)
        if m is not None:
            # remove the host name
            job.LocalOwner = m.group(1).split("@")[0]
        m = re.search("Account_Name = (\S+)", jobString)
        if m is not None:
            job.Extension["LocalAccount"] = m.group(1)
        m = re.search("queue = (\S+)", jobString)
        if m is not None:
            job.Queue = m.group(1)
        m = re.search("job_state = (\S+)", jobString)
        if m is not None:
            state = m.group(1)
            if state == "C":
                # C is completing after having run
                job.State = [
                    computing_activity.ComputingActivity.STATE_FINISHED]
            elif state == "E":
                # E is exiting after having run
                job.State = [
                    computing_activity.ComputingActivity.STATE_TERMINATED]  # ?
            elif state == "Q":
                job.State = [
                    computing_activity.ComputingActivity.STATE_PENDING]
            elif state == "R":
                job.State = [
                    computing_activity.ComputingActivity.STATE_RUNNING]
            elif state == "T":
                job.State = [
                    computing_activity.ComputingActivity.STATE_PENDING]
            elif state == "Q":
                job.State = [
                    computing_activity.ComputingActivity.STATE_PENDING]
            elif state == "S":
                job.State = [
                    computing_activity.ComputingActivity.STATE_SUSPENDED]
            elif state == "H":
                job.State = [computing_activity.ComputingActivity.STATE_HELD]
            else:
                step.warning("found unknown PBS job state '%s'", state)
                job.State = [
                    computing_activity.ComputingActivity.STATE_UNKNOWN]
            job.State.append("pbs:"+state)
        # Just ncpus for some PBS installs. Both at other installs, with different values.
        m = re.search("Resource_List.ncpus = (\d+)", jobString)
        if m is not None:
            job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.size = (\d+)", jobString)
        if m is not None:
            slots = int(m.group(1))
            if job.RequestedSlots is None or slots > job.RequestedSlots:
                job.RequestedSlots = slots
        m = re.search("Resource_List.nodes = (\d+):ppn=(\d+)", jobString)
        if m is not None:
            slots = int(m.group(1)) * int(m.group(2))
            if job.RequestedSlots is None or slots > job.RequestedSlots:
                job.RequestedSlots = slots
        m = re.search("Resource_List.nodes = (\d+)", jobString)
        if m is not None:
            if job.RequestedSlots is None or int(m.group(1)) > job.RequestedSlots:
                job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.nodect = (\d+)", jobString)
        if m is not None:
            if job.RequestedSlots is None or int(m.group(1)) > job.RequestedSlots:
                job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.walltime = (\S+)", jobString)
        if m is not None:
            wall_time = cls._getDuration(m.group(1))
            if job.RequestedSlots is not None:
                job.RequestedTotalWallTime = wall_time * job.RequestedSlots
        m = re.search("resource_used.walltime = (\S+)", jobString)
        if m is not None:
            used_wall_time = cls._getDuration(m.group(1))
            if job.RequestedSlots is not None:
                job.UsedTotalWallTime = used_wall_time * job.RequestedSlots
        m = re.search("resource_used.cput = (\S+)", jobString)
        if m is not None:
            job.UsedTotalCPUTime = cls._getDuration(m.group(1))

        # etime - time job was queued
        m = re.search("etime = (.+)", jobString)
        if m is not None:
            job.SubmissionTime = cls._getDateTime(m.group(1))
            job.ComputingManagerSubmissionTime = job.SubmissionTime
        else:
            # ctime - time job was created
            m = re.search("ctime = (.+)", jobString)
            if m is not None:
                job.SubmissionTime = cls._getDateTime(m.group(1))
                job.ComputingManagerSubmissionTime = job.SubmissionTime

        # qtime - time job became eligible to run

        # start_time - time job started to run
        m = re.search("start_time = (.+)", jobString)
        if m is not None:
            job.StartTime = cls._getDateTime(m.group(1))
        m = re.search("mtime = (.+)", jobString)
        if m is not None:
            if (job.State[0] == computing_activity.ComputingActivity.STATE_FINISHED) or \
                    (job.State[0] == computing_activity.ComputingActivity.STATE_TERMINATED):
                # this is right for terminated since terminated is set on the E state
                job.ComputingManagerEndTime = cls._getDateTime(m.group(1))

        m = re.search("exec_host = (\S+)", jobString)
        if m is not None:
            # exec_host = c013.cm.cluster/7+c013.cm.cluster/6+...
            nodes = set([s.split("/")[0] for s in m.group(1).split("+")])
            job.ExecutionNode = list(nodes)

        return job

    @classmethod
    def _getDuration(cls, dStr):
        (hour, minute, second) = dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

    monthDict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                 "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    @classmethod
    def _getDateTime(cls, dt_str):
        # Example: Fri May 30 06:54:25 2008  (day of the month isn't padded)
        dt = datetime.datetime.strptime(dt_str, "%a %b %d %H:%M:%S %Y")
        return dt.replace(tzinfo=localtzoffset())

#######################################################################################################################


class ComputingActivityUpdateStep(computing_activity.ComputingActivityUpdateStep):

    def __init__(self):
        computing_activity.ComputingActivityUpdateStep.__init__(self)

        self._acceptParameter(
            "server_logs_dir", "the path to the PBS spool/server_logs directory (optional)", False)
        # qstat is needed by ComputingActivitiesStep
        self._acceptParameter(
            "qstat", "the path to the PBS qstat program (default 'qstat')", False)

        # caching job information isn't great with very large queues,
        # but want to provide full information in each job update
        self.activities = {}

    def _run(self):
        try:
            dir_name = self.params["server_logs_dir"]
        except KeyError:
            if "PBS_HOME" not in os.environ:
                raise StepError(
                    "server_logs_dir not specified and the PBS_HOME environment variable is not set")
            dir_name = os.path.join(
                os.environ["PBS_HOME"], "spool", "server_logs")
            if not os.path.exists(dir_name):
                dir_name = os.path.join(os.environ["PBS_HOME"], "server_logs")
                if not os.path.exists(dir_name):
                    raise StepError(
                        "could not find server_logs dir starting from the directory PBS_HOME")

        watcher = LogDirectoryWatcher(
            self._logEntry, dir_name, self.position_file)
        watcher.run()

    def _logEntry(self, log_file_name, entry):
        # log time
        # entry type
        # source (PBS_Server, ...)
        # Svr/Req/Job
        # ? job id (with Job)
        # message
        # It is necessary for Torque to log at the correct level in order for IPF
        # to be able to parse the messages that it uses in determining state.
        # Furthermore, the logging level of Torque can be confusing, as it has
        # both a log_level and a log_events (which is a bitmask).  The most
        # important setting is that log_events should be set to 255.  This
        # ensures that all types of events are logged.  You can check the setting
        # on your Torque installation by using "qmgr".
        toks = entry.split(";")
        if len(toks) < 6:
            self.warning("too few tokens in line: %s", entry)
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
        m = re.search("job (\S+) ", toks[5])
        if m is None:
            return
        id = m.group(1).split(".")[0]  # just the id part of id.host.name
        activity = self._getActivity(id)
        m = re.search(" \(nodelist=([^\)]+)\)", toks[5])
        if m is None:
            return
        activity.ExecutionNode = list(
            set([s.split("/")[0] for s in m.group(1).split("+")]))

    def _handleJobEntry(self, toks):
        id = toks[4].split(".")[0]  # just the id part of id.host.name
        if id.isdigit():
            activity = self._getActivity(id)
        else:
            self.debug(
                "%s not a valid job id in unhandled log event: %s", id, toks)
            return
        if "Job Queued" in toks[5]:
            if activity.published:
                # this is duplicate information - don't publish it again
                self.info("not publishing duplicate pending for %s",
                          activity.LocalIDFromManager)
                return
            # set state in case qstat gives a different one (e.g. the job is already running)
            activity.State = [
                computing_activity.ComputingActivity.STATE_PENDING]
            # qstat should have set the rest of the job attributes specified in this log entry
            activity.published = True
        elif "Job Run" in toks[5]:
            if len(activity.ExecutionNode) == 0:
                # if _handleRequest isn't being invoked to set ExecutionNode, query the scheduler
                activity = self._queryActivity(id)
            activity.State = [
                computing_activity.ComputingActivity.STATE_RUNNING]
            activity.StartTime = self._getDateTime(toks[0])

        elif "Job deleted" in toks[5]:
            activity.State = [
                computing_activity.ComputingActivity.STATE_TERMINATED]
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            if id in self.activities:
                del self.activities[id]
        elif "JOB_SUBSTATE_EXITING" in toks[5]:
            activity.State = [
                computing_activity.ComputingActivity.STATE_FINISHED]
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            if id in self.activities:
                del self.activities[id]
        elif "Job sent signal SIGKILL on delete" in toks[5]:
            # job ran too long and was killed
            activity.State = [
                computing_activity.ComputingActivity.STATE_TERMINATED]
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            if id in self.activities:
                del self.activities[id]
        elif "Job Modified" in toks[5]:
            # when nodes aren't available, log has jobs that quickly go from Job Queued to Job Run to Job Modified
            # and the jobs are pending after this
            if len(activity.State) > 0 and activity.State[0] == computing_activity.ComputingActivity.STATE_RUNNING:
                activity.State[0] = computing_activity.ComputingActivity.STATE_PENDING
                activity.StartTime = None
            else:
                # seems like we can safely ignore others
                return
        elif "Job moved" in toks[5]:
            m = re.search("Job moved to (\S+) at request", toks[5])
            if m is None or m.group(1) == activity.Queue:
                return
            activity.Queue = m.group(1)
        else:
            self.debug("unhandled log event: %s", toks)
            return

        if activity.Queue is None or self._includeQueue(activity.Queue):
            self.output(activity)

    def _getActivity(self, id):
        try:
            activity = self.activities[id]
            # activity will be modified - update creation time
            activity.CreationTime = datetime.datetime.now(localtzoffset())
        except KeyError:
            activity = self._queryActivity(id)
        return activity

    def _queryActivity(self, id):
        qstat = self.params.get("qstat", "qstat")
        cmd = qstat + " -f " + id
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            self.warning("qstat failed: "+output+"\n")
            activity = computing_activity.ComputingActivity()
            activity.LocalIDFromManager = id
        else:
            activity = ComputingActivitiesStep._getJob(output, self)
        self.activities[id] = activity
        activity.published = False
        return activity

    def _getDateTime(self, dt_str):
        # Example: 06/10/2012 16:17:41
        m = re.search("(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)", dt_str)
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


class ComputingSharesStep(computing_share.ComputingSharesStep):

    def __init__(self):
        computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter(
            "qstat", "the path to the PBS qstat program (default 'qstat')", False)

    def _run(self):
        qstat = self.params.get("qstat", "qstat")
        cmd = qstat + " -Q -f -M"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            self.error("qstat failed: "+output)
            raise StepError("qstat failed: "+output+"\n")

        queueStrings = output.split("\n\n")

        queues = []
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if self._includeQueue(queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = computing_share.ComputingShare()

        m = re.search("^Queue: (\S+)", queueString, re.MULTILINE)
        if m is not None:
            queue.Name = m.group(1)
            queue.MappingQueue = queue.Name

        m = re.search("^\s+queue_type = (\S+)", queueString, re.MULTILINE)
        if m is not None:
            queue.Extension["QueueType"] = m.group(1)

        m = re.search("^\s+Priority = (\S+)", queueString, re.MULTILINE)
        if m is not None:
            queue.Extension["Priority"] = int(m.group(1))

        m = re.search("^\s+from_route_only = (\S+)", queueString, re.MULTILINE)
        if m is not None:
            if m.group(1) == "True":
                queue.Extension["FromRouteOnly"] = True
            else:
                queue.Extension["FromRouteOnly"] = False
        m = re.search("^\s+route_destinations = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.Extension["RouteDestinations"] = m.group(1).split(",")

        m = re.search("^\s+resources_max.cput = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.MaxTotalCPUTime = self._getDuration(
                m.group(1))  # cput is for all processes

        m = re.search("^\s+resources_min.walltime = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.MinWallTime = self._getDuration(m.group(1))
        m = re.search("^\s+resources_max.walltime = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.MaxWallTime = self._getDuration(m.group(1))
        m = re.search("^\s+resources_default.walltime = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.DefaultWallTime = self._getDuration(m.group(1))

        m = re.search("^\s+resources_min.ncpus = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.MinSlotsPerJob = int(m.group(1))
        m = re.search("^\s+resources_max.ncpus = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.MaxSlotsPerJob = int(m.group(1))
        m = re.search("^\s+resources_default.ncpus = (\S+)",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.DefaultSlotsPerJob = int(m.group(1))

        m = re.search("^\s+resources_max.mem = (\S+)mb",
                      queueString, re.MULTILINE)
        if m is not None:
            queue.MaxMainMemory = int(m.group(1))

        m = re.search("^\s+max_running = (\S+)", queueString, re.MULTILINE)
        if m is not None:
            queue.MaxRunningJobs = int(m.group(1))

        m = re.search("^\s+total_jobs = (\S+)", queueString, re.MULTILINE)
        if m is not None:
            queue.TotalJobs = int(m.group(1))
        m = re.search("^\s+state_count = (.+)", queueString, re.MULTILINE)
        if m is not None:
            state_count = m.group(1)
            running = 0
            waiting = 0
            m = re.search("Transit:(\S+)", state_count)
            waiting += int(m.group(1))
            m = re.search("Queued:(\S+)", state_count)
            waiting += int(m.group(1))
            m = re.search("Held:(\S+)", state_count)
            waiting += int(m.group(1))
            m = re.search("Waiting:(\S+)", state_count)
            waiting += int(m.group(1))
            m = re.search("Running:(\S+)", state_count)
            running += int(m.group(1))
            queue.RunningJobs = running
            queue.WaitingJobs = waiting

        m = re.search("^\s+enabled = (\S+)", queueString, re.MULTILINE)
        if m is not None:
            if m.group(1) == "True":
                enabled = True
            else:
                enabled = False
            m = re.search("^\s+started = (\S+)", queueString, re.MULTILINE)
            if m is not None:
                if m.group(1) == "True":
                    if enabled:
                        queue.ServingState = "production"
                    else:
                        queue.ServingState = "draining"
                else:
                    if enabled:
                        queue.ServingState = "queueing"
                    else:
                        queue.ServingState = "closed"

        return queue

    def _getDuration(self, dStr):
        (hour, minute, second) = dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

#######################################################################################################################


class ExecutionEnvironmentsStep(execution_environment.ExecutionEnvironmentsStep):
    def __init__(self):
        execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter(
            "pbsnodes", "the path to the PBS pbsnodes program (default 'pbsnodes')", False)
        self._acceptParameter("nodes",
                              "An expression describing the nodes to include (optional). The syntax is a series of +<property> and -<property> where <property> is the name of a node property or a '*'. '+' means include '-' means exclude. The expression is processed in order and the value for a node at the end determines if it is shown.",
                              False)

    def _run(self):
        pbsnodes = self.params.get("pbsnodes", "pbsnodes")

        cmd = pbsnodes + " -a"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            self.error("pbsnodes failed: "+output)
            raise StepError("pbsnodes failed: "+output+"\n")

        nodeStrings = output.split("\n\n")
        hosts = list(map(self._getHost, nodeStrings))
        hosts = list(filter(self._testProperties, hosts))
        hosts = list(filter(self._goodHost, hosts))
        return self._groupHosts(hosts)

    def _getHost(self, nodeString):
        host = execution_environment.ExecutionEnvironment()

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
                    # don't have enough info to do anything else...
                    host.LogicalCPUs = host.PhysicalCPUs
            if line.find("resources_available.mem =") >= 0:
                memSize = line.split("=")[1]
                host.MainMemorySize = int(
                    memSize[:len(memSize)-2]) / 1024  # assuming KB
            if line.find("resources_available.vmem =") >= 0:
                memSize = line.split("=")[1]
                host.VirtualMemorySize = int(
                    memSize[:len(memSize)-2]) / 1024  # assuming KB
            if line.find("status =") >= 0:
                toks = line[14:].split(",")
                for tok in toks:
                    if tok.find("totmem=") >= 0:
                        memSize = tok.split("=")[1]
                        # assuming KB
                        totMem = int(memSize[:len(memSize)-2]) / 1024
                    if tok.find("physmem=") >= 0:
                        memSize = tok.split("=")[1]
                        host.MainMemorySize = int(
                            memSize[:len(memSize)-2]) / 1024  # assuming KB
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
                            # don't have enough info to do anything else...
                            host.LogicalCPUs = host.PhysicalCPUs
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
        nodes = self.params.get("nodes", "+*")
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


class AcceleratorEnvironmentsStep(accelerator_environment.AcceleratorEnvironmentsStep):
    def __init__(self):
        accelerator_environment.AcceleratorEnvironmentsStep.__init__(self)

        self._acceptParameter(
            "scontrol", "the path to the SLURM scontrol program (default 'scontrol')", False)

    def _run(self):
        # get info on the nodes
        return

#######################################################################################################################


class ComputingManagerAcceleratorInfoStep(computing_manager_accel_info.ComputingManagerAcceleratorInfoStep):

    def __init__(self):
        computing_manager_accel_info.ComputingManagerAcceleratorInfoStep.__init__(
            self)

    def _run(self):
        manager_accel_info = computing_manager_accel_info.ComputingManagerAcceleratorInfo()

        return manager_accel_info

#######################################################################################################################


class ComputingShareAcceleratorInfoStep(computing_share_accel_info.ComputingShareAcceleratorInfoStep):

    def __init__(self):
        computing_share_accel_info.ComputingShareAcceleratorInfoStep.__init__(
            self)

    def _run(self):
        share_accel_info = computing_share_accel_info.ComputingShareAcceleratorInfo()
        return share_accel_info

#######################################################################################################################
