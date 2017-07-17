
###############################################################################
#   Copyright 2015 The University of Texas at Austin                          #
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
import itertools
import os
import re

import ipf.dt
from ipf.error import StepError
from ipf.log import LogFileWatcher

from . import computing_activity
from . import computing_manager
from . import computing_service
from . import computing_share
from . import execution_environment

#######################################################################################################################

class ComputingServiceStep(computing_service.ComputingServiceStep):

    def __init__(self):
        computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = computing_service.ComputingService()
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

class ComputingManagerStep(computing_manager.ComputingManagerStep):

    def __init__(self):
        computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = computing_manager.ComputingManager()
        manager.ProductName = "SLURM"
        manager.Name = "SLURM"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(computing_activity.ComputingActivitiesStep):

    def __init__(self):
        computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)

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
            if job.State[0] == computing_activity.ComputingActivity.STATE_PENDING or \
                    job.State[0] == computing_activity.ComputingActivity.STATE_HELD:
                job.WaitingPosition = waiting_pos
                waiting_pos += 1

        return jobs

def _getJob(step, job_str):
    job = computing_activity.ComputingActivity()

    m = re.search("JobId=(\S+)",job_str)
    if m is not None:
        job.LocalIDFromManager = m.group(1)
    m = re.search(" Name=(\S+)",job_str)
    if m is not None:
        job.Name = m.group(1)
    else:
        m = re.search(" JobName=(\S+)",job_str)
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
    m = re.search("Reservation=(\S+)",job_str)
    if m is not None and m.group(1) != "(null)":
        job.Extension["ReservationName"] = m.group(1)
        job.ResourceID = "urn:glue2:ExecutionEnvironment:%s.%s" % (m.group(1),step.resource_name)
    m = re.search("JobState=(\S+)",job_str)
    if m is not None:
        state = m.group(1)  # see squeue man page for state descriptions
        if state == "CANCELLED":
            job.State = [computing_activity.ComputingActivity.STATE_TERMINATED]
        elif state == "COMPLETED":
            job.State = [computing_activity.ComputingActivity.STATE_FINISHED]
        elif state == "CONFIGURING":
            job.State = [computing_activity.ComputingActivity.STATE_STARTING]
        elif state == "COMPLETING":
            job.State = [computing_activity.ComputingActivity.STATE_FINISHING]
        elif state == "FAILED":
            job.State = [computing_activity.ComputingActivity.STATE_FAILED]
        elif state == "NODE_FAIL":
            job.State = [computing_activity.ComputingActivity.STATE_FAILED]
        elif state == "PENDING":
            m = re.search("Reason=Dependency",job_str)
            if m is None:
                job.State = [computing_activity.ComputingActivity.STATE_PENDING]
            else:
                job.State = [computing_activity.ComputingActivity.STATE_HELD]
                # could add what the dependency is
        elif state == "PREEMPTED":
            job.State = [computing_activity.ComputingActivity.STATE_TERMINATED]
        elif state == "REQUEUE_HOLD":
            job.State = [computing_activity.ComputingActivity.STATE_HELD]
        elif state == "RUNNING":
            job.State = [computing_activity.ComputingActivity.STATE_RUNNING]
        elif state == "SUSPENDED":
            job.State = [computing_activity.ComputingActivity.STATE_SUSPENDED]
        elif state == "TIMEOUT":
            job.State = [computing_activity.ComputingActivity.STATE_FINISHED]
        else:
            step.warning("found unknown job state '%s'",state)
            job.State = [computing_activity.ComputingActivity.STATE_UNKNOWN]
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
        if job.State[0] != computing_activity.ComputingActivity.STATE_PENDING:
            job.StartTime = _getDateTime(m.group(1))
    # SLURM sets EndTime to StartTime+TimeLimit while the job is running, so ignore it then
    if job.State != computing_activity.ComputingActivity.STATE_RUNNING:
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
                             tzinfo=ipf.dt.localtzoffset())

#######################################################################################################################

class ComputingActivityUpdateStep(computing_activity.ComputingActivityUpdateStep):

    def __init__(self):
        computing_activity.ComputingActivityUpdateStep.__init__(self)

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
            activity.State = [computing_activity.ComputingActivity.STATE_PENDING]
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
            activity.State = [computing_activity.ComputingActivity.STATE_RUNNING]
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
            activity.State = [computing_activity.ComputingActivity.STATE_TERMINATED]
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
               activity.State[0] == computing_activity.ComputingActivity.STATE_TERMINATED:
                return
            activity.State = [computing_activity.ComputingActivity.STATE_FINISHED]
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
            activity.CreationTime = datetime.datetime.now(ipf.dt.tzoffset(0))
        except KeyError:
            scontrol = self.params.get("scontrol","scontrol")
            cmd = scontrol + " show job "+job_id
            self.debug("running "+cmd)
            status, output = commands.getstatusoutput(cmd)
            if status != 0:
                self.warning("scontrol failed: "+output+"\n")
                activity = computing_activity.ComputingActivity()
                activity.LocalIDFromManager = job_id
            else:
                activity = _getJob(self,output)
            self.activities[activity.LocalIDFromManager] = activity
        return activity

#######################################################################################################################

class ComputingSharesStep(computing_share.ComputingSharesStep):

    def __init__(self):
        computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)

    def _run(self):
        # create shares for partitions
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show partition"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        partition_strs = output.split("\n\n")
        partitions = filter(lambda share: self._includeQueue(share.Name),map(self._getShare,partition_strs))

        # create shares for reservations
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show reservation"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        reservation_strs = output.split("\n\n")
        try:
            reservations = map(self._getReservation,reservation_strs)
        except:
            reservations = []

        return partitions + reservations

    def _getShare(self, partition_str):
        share = computing_share.ComputingShare()

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

    def _getReservation(self, rsrv_str):
        share = computing_share.ComputingShare()
        share.Extension["Reservation"] = True

        m = re.search("ReservationName=(\S+)",rsrv_str)
        if m is None:
            raise StepError("didn't find 'ReservationName'")
        share.Name = m.group(1)
        share.ResourceID = ["urn:glue2:ExecutionEnvironment:%s.%s" % (share.Name,self.resource_name)]
        m = re.search("PartitionName=(\S+)",rsrv_str)
        if m is not None:                                                                                              
            share.MappingQueue = m.group(1)
        m = re.search("NodCnt=(\S+)",rsrv_str)
        if m is not None:
            share.MaxSlotsPerJob = int(m.group(1))

        m = re.search("State=(\S+)",rsrv_str)
        if m is not None:
            if m.group(1) == "ACTIVE":
                share.ServingState = "production"
            elif m.group(1) == "INACTIVE":
                m = re.search("StartTime=(\S+)",rsrv_str)
                if m is not None:
                    start_time = _getDateTime(m.group(1))
                    now = datetime.datetime.now(ipf.dt.localtzoffset())
                    if start_time > now:
                        share.ServingState = "queueing"
                    else:
                        share.ServingState = "closed"
        return share

#######################################################################################################################

class ExecutionEnvironmentsStep(execution_environment.ExecutionEnvironmentsStep):
    def __init__(self):
        execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)

    def _run(self):
        # get info on the nodes
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show node"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        node_strs = output.split("\n\n")
        nodes = filter(self._goodHost,map(self._getNode,node_strs))

        # ignore partitions for now since a node can be part of more than one of them (plus a reservation)

        # create environments for reservations
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show reservation"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        reservation_strs = output.split("\n\n")
        try:
            reservations = map(self._getReservation,reservation_strs)
        except:
            reservations = []

        node_map = {}
        for node in nodes:
            node_map[node.Name] = node
        for exec_env in reservations:
            try:
                node_names = exec_env.Extension["Nodes"]
            except KeyError:
                continue

            # in case a node is in multiple active reservations
            node_names = filter(lambda node_name: node_name in node_map,node_names)

            # in case all of the nodes in the reservation have already been counted
            if len(node_names) == 0:
                continue

            example_node = node_map[node_names[0]]

            exec_env.ConnectivityIn = example_node.ConnectivityIn
            exec_env.ConnectivityOut = example_node.ConnectivityOut
            exec_env.OSName = example_node.OSName
            exec_env.OSVersion = example_node.OSVersion
            exec_env.Platform = example_node.Platform

            exec_env.PhysicalCPUs = sum(map(lambda node_name: node_map[node_name].PhysicalCPUs,
                                            node_names)) / len(node_names)
            exec_env.LogicalCPUs = sum(map(lambda node_name: node_map[node_name].LogicalCPUs,
                                           node_names)) / len(node_names)
            exec_env.MainMemorySize = sum(map(lambda node_name: node_map[node_name].MainMemorySize,
                                              node_names)) / len(node_names)
            exec_env.TotalInstances = len(node_names)
            exec_env.UsedInstances = sum(map(lambda node_name: node_map[node_name].UsedInstances,node_names))
            exec_env.UnavailableInstances = sum(map(lambda node_name: node_map[node_name].UnavailableInstances,
                                                    node_names))
            # remove nodes that are part of a current reservation so that they aren't counted twice
            for node_name in node_names:
                try:
                    del node_map[node_name]
                except KeyError:
                    self.warning("didn't find %s in remaining nodes" % node_name)

            # don't need to publish the node names
            del exec_env.Extension["Nodes"]

        # group up nodes that aren't part of a current reservation
        return reservations + self._groupHosts(node_map.values())

    def _getNode(self, node_str):
        node = execution_environment.ExecutionEnvironment()

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
        m = re.search("RealMemory=(\S+)",node_str)  # MB
        if m is not None:
            node.MainMemorySize = int(m.group(1))
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
            elif "RESERVED" in state:
                node.UsedInstances = 0
                node.UnavailableInstances = 0
            elif "MIXED" in state:
                node.UsedInstances = 1
                node.UnavailableInstances = 0
            else:
                self.warning("unknown node state: %s",state)
                node.UsedInstances = 0
                node.UnavailableInstances = 1

        return node

    # not being used right now
    def _getPartition(self, partition_str):
        partition = execution_environment.ExecutionEnvironment()

        # ID set by ExecutionEnvironment
        m = re.search("PartitionName=(\S+)",partition_str)
        if m is not None:
            partition.Name = m.group(1)

        m = re.search("TotalNodes=(\S+)",partition_str)
        if m is not None and m.group(1) != "(null)":
            partition.TotalInstances = int(m.group(1))

        m = re.search("\sNodes=(\S+)",partition_str)
        if m is not None and m.group(1) != "(null)":
            partition.Extension["Nodes"] = self._expandNames(m.group(1))

        return partition

    def _getReservation(self, rsrv_str):
        rsrv = execution_environment.ExecutionEnvironment()
        rsrv.Extension["Reservation"] = True

        # ID set by ExecutionEnvironment
        m = re.search("ReservationName=(\S+)",rsrv_str)
        if m is None:
            raise StepError("didn't find 'ReservationName'")
        rsrv.Name = m.group(1)
        rsrv.ShareID = ["urn:glue2:ComputingShare:%s.%s" % (rsrv.Name,self.resource_name)]

        m = re.search("StartTime=(\S+)",rsrv_str)
        if m is not None:
            rsrv.Extension["StartTime"] = _getDateTime(m.group(1))
        m = re.search("EndTime=(\S+)",rsrv_str)
        if m is not None:
            rsrv.Extension["EndTime"] = _getDateTime(m.group(1))

        m = re.search("NodeCnt=(\S+)",rsrv_str)
        if m is not None:
            rsrv.Extension["RequestedInstances"] = int(m.group(1))

        m = re.search("Nodes=(\S+)",rsrv_str)
        if m is not None:
            if m.group(1) != "(null)":
                rsrv.Extension["Nodes"] = self._expandNames(m.group(1))

        m = re.search("State=(\S+)",rsrv_str)
        if m is not None:
            if m.group(1) != "ACTIVE":
                if "Nodes" in rsrv.Extension:
                    del rsrv.Extension["Nodes"]   # not active, so no nodes at the current time

        return rsrv

    def _expandNames(self, expr):
        exprs = self._splitCommas(expr)
        if len(exprs) > 1:
            return list(itertools.chain.from_iterable(map(self._expandNames,exprs)))
        m = re.search("^(\S+)\[(\S+)\]$",expr)
        if m is not None:
            prefix = m.group(1)
            suffixes = self._expandNames(m.group(2))
            return map(lambda suffix: prefix+suffix,suffixes)
        m = re.search("^(\d+)-(\d+)$",expr)
        if m is not None:
            # don't drop any leading 0s
            pattern = "%%0%dd" % len(m.group(1))
            return map(lambda num: pattern % num,range(int(m.group(1)),int(m.group(2))+1))
        return [expr]

    def _splitCommas(self, expr):
        exprs = []
        start_pos = 0
        depth = 0
        for pos in range(len(expr)):
            if expr[pos] == "[":
                depth += 1
            elif expr[pos] == "]":
                depth -= 1
            elif expr[pos] == ",":
                if depth == 0:
                    exprs.append(expr[start_pos:pos])
                    start_pos = pos + 1
        exprs.append(expr[start_pos:])
        return exprs

#######################################################################################################################
