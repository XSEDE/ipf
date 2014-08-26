
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
from ipf.log import LogFileWatcher

import glue2.computing_activity
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
from glue2.execution_environment import *

#######################################################################################################################

class ComputingServiceStep(glue2.computing_service.ComputingServiceStep):

    def __init__(self):
        glue2.computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = glue2.computing_service.ComputingService()
        service.Name = "SLURM"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "ipf.SLURM"
        service.QualityLevel = "production"

        return service
        
#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "SLURM"
        manager.Name = "SLURM"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM squeue program (default 'scontrol')",False)

    def _run(self):
        # squeue command doesn't provide submit time
        scontrol = self.params.get("scontrol","scontrol")

        cmd = scontrol + " show job"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")

        jobs = []
        for job_str in output.split("\n\n"):
            job = _getJob(self,job_str)
            if self._includeQueue(job.Queue):
                jobs.append(job)

        # scontrol doesn't sort jobs, so sort them by priority, job id, and state before returning
        jobs = sorted(jobs,key=lambda job: int(job.LocalIDFromManager))
        jobs = sorted(jobs,key=lambda job: -job.Extension["Priority"])
        jobs = sorted(jobs,key=self._jobStateKey)

        # loop through and set WaitingPosition for waiting jobs
        waiting_pos = 1
        for job in jobs:
            if job.State[0] == glue2.computing_activity.ComputingActivity.STATE_PENDING or \
                    job.State[0] == glue2.computing_activity.ComputingActivity.STATE_HELD:
                job.WaitingPosition = waiting_pos
                waiting_pos += 1

        return jobs

def _getJob(step, job_str):
    job = glue2.computing_activity.ComputingActivity()

    m = re.search("JobId=(\S+)",job_str)
    if m is not None:
        job.LocalIDFromManager = m.group(1)
    m = re.search(" Name=(\S+)",job_str)
    if m is not None:
        job.Name = m.group(1)
    m = re.search("UserId=(\S+)\(",job_str)
    if m is not None:
        job.LocalOwner = m.group(1)
    m = re.search("Account=(\S+)",job_str)
    if m is not None:
        job.Extension["LocalAccount"] = m.group(1)
    m = re.search("Partition=(\S+)",job_str)
    if m is not None:
        job.Queue = m.group(1)
    m = re.search("JobState=(\S+)",job_str)
    if m is not None:
        state = m.group(1)  # see squeue man page for state descriptions
        if state == "CANCELLED":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
        elif state == "COMPLETED":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED]
        elif state == "CONFIGURING":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_STARTING]
        elif state == "COMPLETING":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHING]
        elif state == "FAILED":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_FAILED]
        elif state == "NODE_FAIL":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_FAILED]
        elif state == "PENDING":
            m = re.search("Reason=Dependency",job_str)
            if m is None:
                job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
            else:
                job.State = [glue2.computing_activity.ComputingActivity.STATE_HELD]
                # could add what the dependency is
        elif state == "PREEMPTED":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
        elif state == "RUNNING":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
        elif state == "SUSPENDED":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_SUSPENDED]
        elif state == "TIMEOUT":
            job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED]
        else:
            step.warning("found unknown job state '%s'",state)
            job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
        job.State.append("slurm:"+state)

    m = re.search("NumCPUs=(\d+)",job_str)
    if m is not None:
        job.RequestedSlots = int(m.group(1))
    m = re.search("TimeLimit=(\S+)",job_str)
    if m is not None:
        wall_time = _getDuration(m.group(1))
        if job.RequestedSlots is not None:
            job.RequestedTotalWallTime = wall_time * job.RequestedSlots
    m = re.search("RunTime=(\S+)",job_str)
    if m is not None and m.group(1) != "INVALID":
        used_wall_time = _getDuration(m.group(1))
        if used_wall_time > 0 and job.RequestedSlots is not None:
            job.UsedTotalWallTime = used_wall_time * job.RequestedSlots
    m = re.search("SubmitTime=(\S+)",job_str)
    if m is not None:
        job.SubmissionTime = _getDateTime(m.group(1))
        job.ComputingManagerSubmissionTime = job.SubmissionTime
    m = re.search("StartTime=(\S+)",job_str)
    if m is not None and m.group(1) != "Unknown":
        # ignore if job hasn't started (it is an estimated start time used for backfill scheduling)
        if job.State[0] != glue2.computing_activity.ComputingActivity.STATE_PENDING:
            job.StartTime = _getDateTime(m.group(1))
    m = re.search("EndTime=(\S+)",job_str)
    if m is not None and m.group(1) != "Unknown":
        job.EndTime = _getDateTime(m.group(1))
        job.ComputingManagerEndTime = job.EndTime

    # not sure how to interpret NodeList yet
    #m = re.search("exec_host = (\S+)",job_str)
    #if m is not None:
    #    # exec_host = c013.cm.cluster/7+c013.cm.cluster/6+...
    #    nodes = set(map(lambda s: s.split("/")[0], m.group(1).split("+")))
    #    job.ExecutionNode = list(nodes)

    m = re.search("Priority=(\S+)",job_str)
    if m is not None:
        job.Extension["Priority"] = int(m.group(1))

    return job

def _getDuration(dstr):
    m = re.search("(\d+)-(\d+):(\d+):(\d+)",dstr)
    if m is not None:
        return int(m.group(4)) + 60 * (int(m.group(3)) + 60 * (int(m.group(2)) + 24 * int(m.group(1))))
    m = re.search("(\d+):(\d+):(\d+)",dstr)
    if m is not None:
        return int(m.group(3)) + 60 * (int(m.group(2)) + 60 * int(m.group(1)))
    raise StepError("failed to parse duration: %s" % dstr)

def _getDateTime(dtStr):
    # Example: 2010-08-04T14:01:54
    
    year = int(dtStr[0:4])
    month = int(dtStr[5:7])
    day = int(dtStr[8:10])
    hour = int(dtStr[11:13])
    minute = int(dtStr[14:16])
    second = int(dtStr[17:19])

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

        self._acceptParameter("slurmctl_log_file","the path to the SLURM control log file (default '/usr/local/slurm/var/slurmctl.log')",False)
        self._acceptParameter("scontrol","the path to the SLURM squeue program (default 'scontrol')",False)

        self.activities = {}

    def _run(self):
        log_file = self.params.get("slurmctl_log_file","/usr/local/slurm/var/slurmctl.log")
        watcher = LogFileWatcher(self._logEntry,log_file,self.position_file)
        watcher.run()

    def _logEntry(self, log_file_name, entry):

        #[2013-04-21T16:14:47] _slurm_rpc_submit_batch_job JobId=618921 usec=12273
        m = re.search("\[(\S+)\] _slurm_rpc_submit_batch_job JobId=(\S+) usec=\d+",entry)
        if m is not None:
            dt = _getDateTime(m.group(1))
            job_id = m.group(2)
            activity = self._getActivity(job_id)
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
            activity.SubmissionTime = _getDateTime(m.group(1))
            activity.ComputingManagerSubmissionTime = activity.SubmissionTime
            # in case scontrol has more info than just at submit time
            activity.StartTime = None
            activity.EndTime = None
            activity.ComputingManagerEndTime = None
            if self._includeQueue(activity.Queue):
                self.output(activity)
            return

        #[2013-04-21T11:51:52] sched: _slurm_rpc_job_step_create: StepId=617701.0 c410-[603,701,803,904] usec=477
        m = re.search("\[(\S+)\] sched: _slurm_rpc_job_step_create: StepId=(\S+).0",entry)
        if m is not None:
            dt = _getDateTime(m.group(1))
            job_id = m.group(2)
            activity = self._getActivity(job_id)
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
            activity.StartTime = _getDateTime(m.group(1))
            # in case scontrol has more info than just at submit time
            activity.EndTime = None
            activity.ComputingManagerEndTime = None
            if self._includeQueue(activity.Queue):
                self.output(activity)
            return

        #[2013-04-21T16:10:43] Job 618861 cancelled from interactive user
        m = re.search("\[(\S+)\] job (\S+) cancelled from interactive user",entry)
        if m is not None:
            dt = _getDateTime(m.group(1))
            job_id = m.group(2)
            activity = self._getActivity(job_id)
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
            activity.StartTime = _getDateTime(m.group(1))
            if self._includeQueue(activity.Queue):
                self.output(activity)
            if job_id in self.activities:
                del self.activities[job_id]
            return

        #[2013-04-21T11:51:53] sched: _slurm_rpc_step_complete StepId=617701.0 usec=43
        m = re.search("\[(\S+)\] sched: _slurm_rpc_step_complete StepId=(\S+).0",entry)
        if m is not None:
            dt = _getDateTime(m.group(1))
            job_id = m.group(2)
            activity = self._getActivity(job_id)
            if len(activity.State) > 0 and \
               activity.State[0] == glue2.computing_activity.ComputingActivity.STATE_TERMINATED:
                return
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED]
            activity.EndTime = _getDateTime(m.group(1))
            activity.ComputingManagerEndTime = activity.EndTime
            if self._includeQueue(activity.Queue):
                self.output(activity)
            if job_id in self.activities:
                del self.activities[job_id]
            return

    def _getActivity(self, job_id):
        try:
            activity = self.activities[job_id]
            # activity will be modified - update creation time
            activity.CreationTime = datetime.datetime.now(tzoffset(0))
        except KeyError:
            scontrol = self.params.get("scontrol","scontrol")
            cmd = scontrol + " show job "+job_id
            self.debug("running "+cmd)
            status, output = commands.getstatusoutput(cmd)
            if status != 0:
                self.warning("scontrol failed: "+output+"\n")
                activity = glue2.computing_activity.ComputingActivity()
                activity.LocalIDFromManager = job_id
            else:
                activity = _getJob(self,output)
            self.activities[activity.LocalIDFromManager] = activity
        return activity

#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):

    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)

    def _run(self):
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show partition"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")

        partition_strs = output.split("\n\n")

        partitions = []
        for partition_str in partition_strs:
            partition = self._getShare(partition_str)
            if self._includeQueue(partition.Name):
                partitions.append(partition)
        return partitions

    def _getShare(self, partition_str):
        share = glue2.computing_share.ComputingShare()

        m = re.search("PartitionName=(\S+)",partition_str)
        if m is not None:
            share.Name = m.group(1)
            share.MappingQueue = share.Name
        m = re.search("MaxNodes=(\S+)",partition_str)
        if m is not None and m.group(1) != "UNLIMITED":
            share.MaxSlotsPerJob = int(m.group(1))
        m = re.search("MaxMemPerNode=(\S+)",partition_str)
        if m is not None and m.group(1) != "UNLIMITED":
            share.MaxMainMemory = int(m.group(1))
        m = re.search("DefaultTime=(\S+)",partition_str)
        if m is not None and m.group(1) != "NONE":
            share.DefaultWallTime = _getDuration(m.group(1))
        m = re.search("MaxTime=(\S+)",partition_str)
        if m is not None and m.group(1) != "UNLIMITED":
            share.MaxWallTime = _getDuration(m.group(1))

        m = re.search("PreemptMode=(\S+)",partition_str)
        if m is not None:
            if m.group(1) == "OFF":
                self.Preemption = False
            else:
                self.Preemption = True

        m = re.search("State=(\S+)",partition_str)
        if m is not None:
            if m.group(1) == "UP":
                share.ServingState = "production"
            else:
                share.ServingState = "closed"

        return share

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):
    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)

    def _run(self):
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show node"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")

        node_strs = output.split("\n\n")
        nodes = map(self._getNode,node_strs)
        nodes = filter(self._goodHost,nodes)
        return nodes

    def _getNode(self, node_str):
        node = glue2.execution_environment.ExecutionEnvironment()

        # ID set by ExecutionEnvironment
        m = re.search("NodeName=(\S+)",node_str)
        if m is not None:
            node.Name = m.group(1)
        m = re.search("Sockets=(\S+)",node_str)
        if m is not None:
            node.PhysicalCPUs = int(m.group(1))
        m = re.search("CPUTot=(\S+)",node_str)
        if m is not None:
            node.LogicalCPUs = int(m.group(1))
        m = re.search("State=(\S+)",node_str)
        if m is not None:
            node.TotalInstances = 1
            state = m.group(1)
            if "IDLE" in state:
                node.UsedInstances = 0
                node.UnavailableInstances = 0
            elif "ALLOCATED" in state:
                node.UsedInstances = 1
                node.UnavailableInstances = 0
            elif "DOWN" in state:
                node.UsedInstances = 0
                node.UnavailableInstances = 1
            elif "MAINT" in state:
                node.UsedInstances = 0
                node.UnavailableInstances = 1
            else:
                self.warning("unknown node state: %s",state)
                node.UsedInstances = 0
                node.UnavailableInstances = 1

        # 'RealMemory' is 1. not sure if this is a bad value or what

        return node

#######################################################################################################################
