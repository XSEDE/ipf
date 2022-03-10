
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

import subprocess
import datetime
import dateutil.parser
import itertools
import os
import re

import ipf.dt
from ipf.error import StepError
from ipf.log import LogFileWatcher

from . import computing_activity
from . import computing_manager
from . import computing_manager_accel_info
from . import computing_service
from . import computing_share
from . import computing_share_accel_info
from . import execution_environment
from . import accelerator_environment


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
        self._acceptParameter("showjob","the path to the SLURM scontrol program (default 'show job')",False)
        self._acceptParameter("JobId","Regular Expression to parse JobId (default JobId=(\S+)')",False)
        self._acceptParameter(" Name","Regular Expression to parse  Name (default  Name=(\S+)')",False)
        self._acceptParameter(" JobName","Regular Expression to parse  JobName (default ' JobName=(\S+)')",False)
        self._acceptParameter("UserId","Regular Expression to parse UserId (default 'UserId=(\S+)\(')",False)
        self._acceptParameter("Account","Regular Expression to parse Account (default 'Account=(\S+)')",False)
        self._acceptParameter("Partition","Regular Expression to parse Partition (default 'Partition=(\S+)')",False)
        self._acceptParameter("Reservation","Regular Expression to parse Reservation (default 'Reservation=(\S+)')",False)
        self._acceptParameter("JobState","Regular Expression to parse JobState (default 'JobState=(\S+)')",False)
        self._acceptParameter("JobHeld","Regular Expression to parse whether Job is HELD (default 'Reason=Dependency')",False)
        self._acceptParameter("NumCPUs","Regular Expression to parse NumCPUs (default 'NumCPUs=(\d+)')",False)
        self._acceptParameter("gresgpu","Regular Expression to parse gres/gpu (default 'gres/gpu=(\d+)')",False)
        self._acceptParameter("TimeLimit","Regular Expression to parse TimeLimit (default 'TimeLimit=(\S+)')",False)
        self._acceptParameter("RunTime","Regular Expression to parse RunTime (default 'RunTime=(\S+)')",False)
        self._acceptParameter("SubmitTime","Regular Expression to parse SubmitTime (default 'SubmitTime=(\S+)')",False)
        self._acceptParameter("StartTime","Regular Expression to parse StartTime (default 'StartTime=(\S+)')",False)
        self._acceptParameter("EndTime","Regular Expression to parse EndTime (default 'EndTime=(\S+)')",False)
        self._acceptParameter("exec_host ","Regular Expression to parse exec_host (default 'exec_host = (\S+)')",False)
        self._acceptParameter("Priority","Regular Expression to parse Priority (default 'Priority=(\S+)')",False)

    def _run(self):
        # squeue command doesn't provide submit time
        scontrol = self.params.get("scontrol","scontrol")
        showjob = self.params.get("showjob","show job")

        cmd = scontrol + " " + showjob
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError(scontrol+" failed: "+output+"\n")

        jobs = []
        for job_str in output.split("\n\n"):
            job = _getJob(self,job_str,self.params)
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

def _getJob(step, job_str,params):
    showjob = params.get("showjob","show job")
    job = computing_activity.ComputingActivity()
    JobId = params.get("JobId","JobId=(\S+)")
    Name = params.get(" Name"," Name=(\S+)")
    JobName = params.get(" JobName"," JobName=(\S+)")
    UserId = params.get("UserId","UserId=(\S+)\(")
    Account = params.get("Account","Account=(\S+)")
    Partition = params.get("Partition","Partition=(\S+)")
    Reservation = params.get("Reservation","Reservation=(\S+)")
    JobState = params.get("JobState","JobState=(\S+)")
    JobHeld = params.get("JobHeld","Reason=Dependency")
    NumCPUs = params.get("NumCPUs","NumCPUs=(\d+)")
    gresgpu = params.get("gresgpu","gres/gpu=(\d+)")
    TimeLimit = params.get("TimeLimit","TimeLimit=(\S+)")
    RunTime = params.get("RunTime","RunTime=(\S+)")
    SubmitTime = params.get("SubmitTime","SubmitTime=(\S+)")
    StartTime = params.get("StartTime","StartTime=(\S+)")
    EndTime = params.get("EndTime","EndTime=(\S+)")
    exec_host  = params.get("exec_host ","exec_host = (\S+)")
    Priority = params.get("Priority","Priority=(\S+)")

    m = re.search(JobId,job_str)
    if m is not None:
        job.LocalIDFromManager = m.group(1)
    m = re.search(Name,job_str)
    if m is not None:
        job.Name = m.group(1)
    else:
        m = re.search(JobName,job_str)
        if m is not None:
            job.Name = m.group(1)
    m = re.search(UserId,job_str)
    if m is not None:
        job.LocalOwner = m.group(1)
    m = re.search(Account,job_str)
    if m is not None:
        job.Extension["LocalAccount"] = m.group(1)
    m = re.search(Partition,job_str)
    if m is not None:
        job.Queue = m.group(1)
        job.ResourceID = "urn:glue2:ExecutionEnvironment:%s.%s" % (m.group(1),step.resource_name)
    m = re.search(Reservation,job_str)
    if m is not None and m.group(1) != "(null)":
        job.Extension["ReservationName"] = m.group(1)
        job.ResourceID = "urn:glue2:ExecutionEnvironment:%s.%s" % (m.group(1),step.resource_name)
    m = re.search(JobState,job_str)
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
            m = re.search(JobHeld,job_str)
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

    m = re.search(NumCPUs,job_str)
    if m is not None:
        job.RequestedSlots = int(m.group(1))
    m = re.search(gresgpu,job_str)
    if m is not None:
        job.RequestedAcceleratorSlots = int(m.group(1))
    m = re.search(TimeLimit,job_str)
    if m is not None:
        wall_time = _getDuration(m.group(1))
        if job.RequestedSlots is not None:
            job.RequestedTotalWallTime = wall_time * job.RequestedSlots
    m = re.search(RunTime,job_str)
    if m is not None and m.group(1) != "INVALID":
        used_wall_time = _getDuration(m.group(1))
        if used_wall_time > 0 and job.RequestedSlots is not None:
            job.UsedTotalWallTime = used_wall_time * job.RequestedSlots
    m = re.search(SubmitTime,job_str)
    if m is not None:
        job.SubmissionTime = _getDateTime(m.group(1))
        job.ComputingManagerSubmissionTime = job.SubmissionTime
    m = re.search(StartTime,job_str)
    if m is not None and m.group(1) != "Unknown":
        # ignore if job hasn't started (it is an estimated start time used for backfill scheduling)
        if job.State[0] != computing_activity.ComputingActivity.STATE_PENDING:
            job.StartTime = _getDateTime(m.group(1))
    # SLURM sets EndTime to StartTime+TimeLimit while the job is running, so ignore it then
    if job.State != computing_activity.ComputingActivity.STATE_RUNNING:
        m = re.search(EndTime,job_str)
        if m is not None and m.group(1) != "Unknown":
            job.EndTime = _getDateTime(m.group(1))
            job.ComputingManagerEndTime = job.EndTime

    # not sure how to interpret NodeList yet
    #m = re.search(exec_host",job_str)
    #if m is not None:
    #    # exec_host = c013.cm.cluster/7+c013.cm.cluster/6+...
    #    nodes = set(map(lambda s: s.split("/")[0], m.group(1).split("+")))
    #    job.ExecutionNode = list(nodes)

    m = re.search(Priority,job_str)
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

    DEFAULTYEAR=datetime.datetime.now(tz=ipf.dt.localtzoffset())
    dt = dateutil.parser.parse(dtStr,default=DEFAULTYEAR)

    return dt

#######################################################################################################################

class ComputingActivityUpdateStep(computing_activity.ComputingActivityUpdateStep):

    def __init__(self):
        computing_activity.ComputingActivityUpdateStep.__init__(self)

        self._acceptParameter("slurmctl_log_file","the path to the SLURM control log file (default '/usr/local/slurm/var/slurmctl.log')",False)
        self._acceptParameter("scontrol","the path to the SLURM squeue program (default 'scontrol')",False)
        self._acceptParameter("submit_batch_job_regexp","regexp to match _slurm_rpc_submit_batch_job lines from slurmctl.log",False)
        self._acceptParameter("job_step_create_regexp","regexp to match _slurm_rpc_job_step_create lines from slurmctl.log",False)
        self._acceptParameter("job_cancelled_regexp","regexp to match cancelled from interactive user lines from slurmctl.log",False)
        self._acceptParameter("step_complete_regexp","regexp to match _slurm_rpc_step_complete lines from slurmctl.log",False)

        self.activities = {}

    def _run(self):
        log_file = self.params.get("slurmctl_log_file","/usr/local/slurm/var/slurmctl.log")
        watcher = LogFileWatcher(self._logEntry,log_file,self.position_file)
        watcher.run()

    def _logEntry(self, log_file_name, entry):
        submit_re = self.params.get("submit_batch_job_regexp","\[(\S+)\] _slurm_rpc_submit_batch_job JobId=(\S+) usec=\d+")
        stepcreate_re = self.params.get("job_step_create_regexp","\[(\S+)\] sched: _slurm_rpc_job_step_create: StepId=(\S+).0")
        cancelled_re = self.params.get("job_cancelled_regexp","\[(\S+)\] job (\S+) cancelled from interactive user")
        stepcomplete_re = self.params.get("step_complete_regexp","\[(\S+)\] sched: _slurm_rpc_step_complete StepId=(\S+).0")
        #[2013-04-21T16:14:47] _slurm_rpc_submit_batch_job JobId=618921 usec=12273

        m = re.search(submit_re,entry)
        if m is not None:
            dt = _getDateTime(m.group(1))
            #DEFAULTYEAR=datetime.datetime.now(tz=ipf.dt.localtzoffset())
            #dt = dateutil.parser.parse(m.group(1),default=DEFAULTYEAR)

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
        m = re.search(stepcreate_re,entry)
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
        m = re.search(cancelled_re,entry)
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
        m = re.search(stepcomplete_re,entry)
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
            showjob = self.params.get("showjob","show job")
            cmd = scontrol + " " +showjob+" "+job_id
            self.debug("running "+cmd)
            status, output = subprocess.getstatusoutput(cmd)
            if status != 0:
                self.warning("scontrol failed: "+output+"\n")
                activity = computing_activity.ComputingActivity()
                activity.LocalIDFromManager = job_id
            else:
                activity = _getJob(self,output,self.params)
            self.activities[activity.LocalIDFromManager] = activity
        return activity

#######################################################################################################################

class ComputingSharesStep(computing_share.ComputingSharesStep):

    def __init__(self):
        computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)
        self._acceptParameter("PartitionName","Regular Expression to parse PartitionName (default 'PartitionName=(\S+)')",False)
        self._acceptParameter("MaxNodes","Regular Expression to parse MaxNodes (default 'MaxNodes=(\S+)')",False)
        self._acceptParameter("MaxMemPerNode","Regular Expression to parse MaxMemPerNode (default 'MaxMemPerNode=(\S+)')",False)
        self._acceptParameter("DefaultTime","Regular Expression to parse DefaultTime (default 'DefaultTime=(\S+)')",False)
        self._acceptParameter("MaxTime","Regular Expression to parse MaxTime (default 'MaxTime=(\S+)')",False)
        self._acceptParameter("PreemptMode","Regular Expression to parse PreemptMode (default 'PreemptMode=(\S+)')",False)
        self._acceptParameter("State","Regular Expression to parse State (default 'State=(\S+)')",False)
        self._acceptParameter("ReservationName","Regular Expression to parse ReservationName (default 'ReservationName=(\S+)')",False)
        self._acceptParameter("NodCnt","Regular Expression to parse NodCnt (default 'NodCnt=(\S+)')",False)
        self._acceptParameter("State","Regular Expression to parse State (default 'State=(\S+)')",False)

    def _run(self):
        # create shares for partitions
        scontrol = self.params.get("scontrol","scontrol")
        PartitionName = self.params.get("PartitionName","PartitionName=(\S+)')")
        MaxNodes = self.params.get("MaxNodes","MaxNodes=(\S+)')")
        MaxMemPerNode = self.params.get("MaxMemPerNode","MaxMemPerNode=(\S+)')")
        DefaultTime = self.params.get("DefaultTime","DefaultTime=(\S+)')")
        MaxTime = self.params.get("MaxTime","MaxTime=(\S+)')")
        State = self.params.get("State","State=(\S+)')")
        ReservationName = self.params.get("ReservationName","ReservationName=(\S+)')")
        PartitionName = self.params.get("PartitionName","PartitionName=(\S+)')")
        NodCnt = self.params.get("NodCnt","NodCnt=(\S+)')")
        State = self.params.get("State","State=(\S+)')")

        cmd = scontrol + " show partition"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        partition_strs = output.split("\n\n")
        partitions = [share for share in map(self._getShare,partition_strs) if self._includeQueue(share.Name)]

        # create shares for reservations
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show reservation"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        reservation_strs = output.split("\n\n")
        try:
            reservations = [self.includeQueue(share.PartitionName) for share in list(map(self._getReservation,reservation_strs))]
        except:
            reservations = []

        self.debug("returning "+ str(partitions + reservations))
        return partitions + reservations

    def _getShare(self, partition_str):
        share = computing_share.ComputingShare()
        PartitionName = self.params.get("PartitionName","PartitionName=(\S+)")
        MaxNodes = self.params.get("MaxNodes","MaxNodes=(\S+)")
        MaxMemPerNode = self.params.get("MaxMemPerNode","MaxMemPerNode=(\S+)")
        DefaultTime = self.params.get("DefaultTime","DefaultTime=(\S+)")
        MaxTime = self.params.get("MaxTime","MaxTime=(\S+)")
        State = self.params.get("State","State=(\S+)")
        ReservationName = self.params.get("ReservationName","ReservationName=(\S+)")
        NodCnt = self.params.get("NodCnt","NodCnt=(\S+)")
        State = self.params.get("State","State=(\S+)")
        PreemptMode = self.params.get("PreemptMode","PreemptMode=(\S+)")

        m = re.search(PartitionName,partition_str)
        if m is not None:
            share.Name = m.group(1)
            share.MappingQueue = share.Name
        m = re.search(MaxNodes,partition_str)
        if m is not None and m.group(1) != "UNLIMITED":
            share.MaxSlotsPerJob = int(m.group(1))
        m = re.search(MaxMemPerNode,partition_str)
        if m is not None and m.group(1) != "UNLIMITED":
            share.MaxMainMemory = int(m.group(1))
        m = re.search(DefaultTime,partition_str)
        if m is not None and m.group(1) != "NONE":
            share.DefaultWallTime = _getDuration(m.group(1))
        m = re.search(MaxTime,partition_str)
        if m is not None and m.group(1) != "UNLIMITED":
            share.MaxWallTime = _getDuration(m.group(1))

        m = re.search(PreemptMode,partition_str)
        if m is not None:
            if m.group(1) == "OFF":
                self.Preemption = False
            else:
                self.Preemption = True

        m = re.search(State,partition_str)
        if m is not None:
            if m.group(1) == "UP":
                share.ServingState = "production"
            else:
                share.ServingState = "closed"

        share.ResourceID = ["urn:glue2:ExecutionEnvironment:%s.%s" % (share.Name,self.resource_name)]
        return share

    def _getReservation(self, rsrv_str):
        share = computing_share.ComputingShare()
        share.Extension["Reservation"] = True

        m = re.search(ReservationName,rsrv_str)
        if m is None:
            raise StepError("didn't find 'ReservationName'")
        share.Name = m.group(1)
        share.ResourceID = ["urn:glue2:ExecutionEnvironment:%s.%s" % (share.Name,self.resource_name)]
        m = re.search(PartitionName,rsrv_str)
        if m is not None:                                                                                              
            share.MappingQueue = m.group(1)
        m = re.search(NodCnt,rsrv_str)
        if m is not None:
            share.MaxSlotsPerJob = int(m.group(1))

        m = re.search(State,rsrv_str)
        if m is not None:
            if m.group(1) == "ACTIVE":
                share.ServingState = "production"
            elif m.group(1) == "INACTIVE":
                m = re.search(StartTime,rsrv_str)
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
        self._acceptParameter("PartitionName","Regular Expression to parse PartitionName (default 'PartitionName=(\S+)')",False)
        self._acceptParameter("TotalNodes","Regular Expression to parse TotalNodes (default 'TotalNodes=(\S+)')",False)
        self._acceptParameter("sNodes","Regular Expression to parse sNodes (default '\sNodes=(\S+)')",False)
        self._acceptParameter("ReservationName","Regular Expression to parse ReservationName (default 'ReservationName=(\S+)')",False)
        self._acceptParameter("StartTime","Regular Expression to parse StartTime (default 'StartTime=(\S+)')",False)
        self._acceptParameter("EndTime","Regular Expression to parse EndTime (default 'EndTime=(\S+)')",False)
        self._acceptParameter("NodeCnt","Regular Expression to parse NodeCnt (default 'NodeCnt=(\S+)')",False)
        self._acceptParameter("Nodes","Regular Expression to parse Nodes (default 'Nodes=(\S+)')",False)
        self._acceptParameter("State","Regular Expression to parse State (default 'State=(\S+)')",False)

    def _run(self):


        # get info on the nodes
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show node -d"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        node_strs = output.split("\n\n")
        nodes = list(filter(self._goodHost,list(map(self._getNode,node_strs))))

        # ignore partitions for now since a node can be part of more than one of them (plus a reservation)
        # create environments for partitions
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show partition"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        partition_strs = output.split("\n\n")
        try:
            partitions = [share for share in map(self._getPartition,partition_strs) if self._includeQueue(share.Name)]
            #partitions = [self._includeQueue(share.Name) for share in list(map(self._getPartition,partition_strs))]
        except Exception as err:
            partitions = []

        # create environments for reservations
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show reservation"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        reservation_strs = output.split("\n\n")
        try:
            #reservations = map(self._getReservation,reservation_strs)
            #reservations = [self.includeQueue(share.PartitionName) for share in list(map(self._getReservation,reservation_strs))]
            reservations = [share for share in map(self._getReservation,reservation_strs) if self._includeQueue(share.PartitionName)]
        except Exception as err:
            reservations = []

        node_map = {}
        for node in nodes:
            node_map[node.Name] = node
        for seq in (partitions,reservations):
          for exec_env in seq:
            try:
                node_names = exec_env.Extension["Nodes"]
            except KeyError:
                continue

            # in case a node is in multiple active reservations
            node_names = [node_name for node_name in node_names if node_name in node_map]

            # in case all of the nodes in the reservation have already been counted
            if len(node_names) == 0:
                continue

            example_node = node_map[node_names[0]]

            exec_env.ConnectivityIn = example_node.ConnectivityIn
            exec_env.ConnectivityOut = example_node.ConnectivityOut
            exec_env.OSName = example_node.OSName
            exec_env.OSVersion = example_node.OSVersion
            exec_env.Platform = example_node.Platform
            if "AvailableFeatures" in example_node.Extension and example_node.Extension["AvailableFeatures"] is not None and example_node.Extension["AvailableFeatures"] != "(null)":
                exec_env.Extension["AvailableFeatures"] = example_node.Extension["AvailableFeatures"]

            exec_env.PhysicalCPUs = sum([node_map[node_name].PhysicalCPUs for node_name in node_names]) / len(node_names)
            exec_env.LogicalCPUs = sum([node_map[node_name].LogicalCPUs for node_name in node_names]) / len(node_names)
            exec_env.MainMemorySize = sum([node_map[node_name].MainMemorySize for node_name in node_names]) / len(node_names)
            exec_env.TotalInstances = len(node_names)
            exec_env.UsedInstances = sum([node_map[node_name].UsedInstances for node_name in node_names])
            exec_env.UnavailableInstances = sum([node_map[node_name].UnavailableInstances for node_name in node_names])
            # remove nodes that are part of a current reservation so that they aren't counted twice
            for node_name in node_names:
                try:
                    del node_map[node_name]
                except KeyError:
                    self.warning("didn't find %s in remaining nodes" % node_name)

            # don't need to publish the node names
            del exec_env.Extension["Nodes"]

        # group up nodes that aren't part of a current reservation
        #return reservations + partitions + self._groupHosts(list(node_map.values()))
        return reservations + partitions 

    def _getNode(self, node_str):
        node = execution_environment.ExecutionEnvironment()
        NodeName = self.params.get("NodeName","NodeName=(\S+)")
        Sockets = self.params.get("Sockets","Sockets=(\S+)")
        CPUTot = self.params.get("CPUTot","CPUTot=(\S+)")
        RealMemory = self.params.get("RealMemory","RealMemory=(\S+)")
        Partitions = self.params.get("Partitions","Partitions=(\S+)")
        State = self.params.get("State","State=(\S+)")

        # ID set by ExecutionEnvironment
        m = re.search(NodeName,node_str)
        if m is not None:
            node.Name = m.group(1)
        m = re.search(Sockets,node_str)
        if m is not None:
            node.PhysicalCPUs = int(m.group(1))
        m = re.search(CPUTot,node_str)
        if m is not None:
            node.LogicalCPUs = int(m.group(1))
        m = re.search(RealMemory,node_str)  # MB
        if m is not None:
            node.MainMemorySize = int(m.group(1))
        m = re.search(Partitions,node_str)
        if m is not None:
            node.Partitions = m.group(1)
        m = re.search("AvailableFeatures=(\S+)",node_str)
        if m is not None:
            node.Extension["AvailableFeatures"] = m.group(1)
        m = re.search(State,node_str)
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

    # ExecutionEnvironment get partition
    def _getPartition(self, partition_str):
        partition = execution_environment.ExecutionEnvironment()
        PartitionName = self.params.get("PartitionName","PartitionName=(\S+)")
        TotalNodes = self.params.get("TotalNodes","TotalNodes=(\S+)")
        Nodes = self.params.get("Nodes","\sNodes=(\S+)")

        # ID set by ExecutionEnvironment
        m = re.search(PartitionName,partition_str)
        if m is not None:
            partition.Name = m.group(1)

        m = re.search(TotalNodes,partition_str)
        if m is not None and m.group(1) != "(null)":
            partition.TotalInstances = int(m.group(1))

        m = re.search(Nodes,partition_str)
        if m is not None and m.group(1) != "(null)":
            partition.Extension["Nodes"] = self._expandNames(m.group(1))

        return partition

    def _getReservation(self, rsrv_str):
        rsrv = execution_environment.ExecutionEnvironment()
        ReservationName = self.params.get("ReservationName","ReservationName=(\S+)")
        StartTime = self.params.get("StartTime","StartTime=(\S+)")
        EndTime = self.params.get("EndTime","EndTime=(\S+)")
        NodeCnt = self.params.get("NodeCnt","NodeCnt=(\S+)")
        Nodes = self.params.get("Nodes","Nodes=(\S+)")
        State = self.params.get("State","State=(\S+)")

        rsrv.Extension["Reservation"] = True

        # ID set by ExecutionEnvironment
        m = re.search(ReservationName,rsrv_str)
        if m is None:
            raise StepError("didn't find 'ReservationName'")
        rsrv.Name = m.group(1)
        rsrv.ShareID = ["urn:glue2:ComputingShare:%s.%s" % (rsrv.Name,self.resource_name)]

        m = re.search(StartTime,rsrv_str)
        if m is not None:
            rsrv.Extension["StartTime"] = _getDateTime(m.group(1))
        m = re.search(EndTime,rsrv_str)
        if m is not None:
            rsrv.Extension["EndTime"] = _getDateTime(m.group(1))

        m = re.search(NodeCnt,rsrv_str)
        if m is not None:
            rsrv.Extension["RequestedInstances"] = int(m.group(1))

        m = re.search(Nodes,rsrv_str)
        if m is not None:
            if m.group(1) != "(null)":
                rsrv.Extension["Nodes"] = self._expandNames(m.group(1))

        m = re.search(State,rsrv_str)
        if m is not None:
            if m.group(1) != "ACTIVE":
                if "Nodes" in rsrv.Extension:
                    del rsrv.Extension["Nodes"]   # not active, so no nodes at the current time

        return rsrv

    def _expandNames(self, expr):
        exprs = self._splitCommas(expr)
        if len(exprs) > 1:
            return list(itertools.chain.from_iterable(list(map(self._expandNames,exprs))))
        m = re.search("^(\S+)\[(\S+)\]$",expr)
        if m is not None:
            prefix = m.group(1)
            suffixes = self._expandNames(m.group(2))
            return [prefix+suffix for suffix in suffixes]
        m = re.search("^(\d+)-(\d+)$",expr)
        if m is not None:
            # don't drop any leading 0s
            pattern = "%%0%dd" % len(m.group(1))
            return [pattern % num for num in range(int(m.group(1)),int(m.group(2))+1)]
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

class ComputingManagerAcceleratorInfoStep(computing_manager_accel_info.ComputingManagerAcceleratorInfoStep):

    def __init__(self):
        computing_manager_accel_info.ComputingManagerAcceleratorInfoStep.__init__(self)

    def _run(self):
        manager_accel_info = computing_manager_accel_info.ComputingManagerAcceleratorInfo()
        #manager.ProductName = "SLURM"
        #manager.Name = "SLURM"
        #manager.Reservation = True
        #self.BulkSubmission = True

        return manager_accel_info

#######################################################################################################################

class ComputingShareAcceleratorInfoStep(computing_share_accel_info.ComputingShareAcceleratorInfoStep):

    def __init__(self):
        computing_share_accel_info.ComputingShareAcceleratorInfoStep.__init__(self)

    def _run(self):
        share_accel_info = computing_share_accel_info.ComputingShareAcceleratorInfo()
        #manager.ProductName = "SLURM"
        #manager.Name = "SLURM"
        #manager.Reservation = True
        #self.BulkSubmission = True

        return share_accel_info

#######################################################################################################################

class AcceleratorEnvironmentsStep(accelerator_environment.AcceleratorEnvironmentsStep):
    def __init__(self):

        accelerator_environment.AcceleratorEnvironmentsStep.__init__(self)

        self._acceptParameter("scontrol","the path to the SLURM scontrol program (default 'scontrol')",False)
        self._acceptParameter("PartitionName","Regular Expression to parse PartitionName (default 'PartitionName=(\S+)')",False)
        self._acceptParameter("TotalNodes","Regular Expression to parse TotalNodes (default 'TotalNodes=(\S+)')",False)
        self._acceptParameter("Nodes","Regular Expression to parse sNodes (default '\sNodes=(\S+)')",False)
        self._acceptParameter("ReservationName","Regular Expression to parse ReservationName (default 'ReservationName=(\S+)')",False)
        self._acceptParameter("StartTime","Regular Expression to parse StartTime (default 'StartTime=(\S+)')",False)
        self._acceptParameter("EndTime","Regular Expression to parse EndTime (default 'EndTime=(\S+)')",False)
        self._acceptParameter("NodeCnt","Regular Expression to parse NodeCnt (default 'NodeCnt=(\S+)')",False)
        self._acceptParameter("Nodes","Regular Expression to parse Nodes (default 'Nodes=(\S+)')",False)
        self._acceptParameter("State","Regular Expression to parse State (default 'State=(\S+)')",False)
        self._acceptParameter("NodeName","Regular Expression to parse NodeName (default 'NodeName=(\S+)')",False)
        self._acceptParameter("Sockets","Regular Expression to parse Sockets (default 'Sockets=(\S+)')",False)
        self._acceptParameter("CPUTot","Regular Expression to parse CPUTot (default 'CPUTot=(\S+)')",False)
        self._acceptParameter("RealMemory","Regular Expression to parse RealMemory (default 'RealMemory=(\S+)')",False)
        self._acceptParameter("Gres","Regular Expression to parse Gres (default 'Gres=(\S+)')",False)
        self._acceptParameter("GresUsed","Regular Expression to parse GresUsed (default 'GresUsed=(\S+)')",False)

    def _run(self):
        # get info on the nodes
#        import rpdb2; rpdb2.start_embedded_debugger("asdf")
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show node -d"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        node_strs = output.split("\n\n")
        nodes = list(filter(self._goodHost,list(map(self._getNode,node_strs))))

        # ignore partitions for now since a node can be part of more than one of them (plus a reservation)
        # create environments for partitions
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show partition"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        partition_strs = output.split("\n\n")
        try:
            partitions = [share for share in map(self._getPartition,partition_strs) if self._includeQueue(share.Name)]
            #partitions = [self._includeQueue(share.Name) for share in list(map(self._getPartition,partition_strs))]
        except Exception as err:
            partitions = []


        # create environments for reservations
        scontrol = self.params.get("scontrol","scontrol")
        cmd = scontrol + " show reservation"
        self.debug("running "+cmd)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            raise StepError("scontrol failed: "+output+"\n")
        reservation_strs = output.split("\n\n")
        try:
            #reservations = map(self._getReservation,reservation_strs)
            reservations = [self.includeQueue(share.PartitionName) for share in list(map(self._getReservation,reservation_strs))]
        except:
            reservations = []

        self.debug("number of reservations "+str(len(reservations)))
        node_map = {}
        for node in nodes:
            node_map[node.Name] = node
        for accel_env in reservations:
            try:
                node_names = accel_env.Extension["Nodes"]
            except KeyError:
                continue
            self.debug("size of node map before defining"+str(len(node_map)))
            # in case a node is in multiple active reservations
            node_names = [node_name for node_name in node_names if node_name in node_map]

            # in case all of the nodes in the reservation have already been counted
            if len(node_names) == 0:
                continue

            example_node = node_map[node_names[0]]

            accel_env.ConnectivityIn = example_node.ConnectivityIn
            accel_env.ConnectivityOut = example_node.ConnectivityOut
            accel_env.OSName = example_node.OSName
            accel_env.OSVersion = example_node.OSVersion
            accel_env.Platform = example_node.Platform

            accel_env.PhysicalCPUs = sum([node_map[node_name].PhysicalCPUs for node_name in node_names]) / len(node_names)
            accel_env.PhysicalAccelerators = sum([node_map[node_name].PhysicalAccelerators for node_name in node_names]) / len(node_names)
            accel_env.UsedAcceleratorSlots = sum([node_map[node_name].UsedAcceleratorSlots for node_name in node_names]) / len(node_names)
            #exec_env.LogicalAccelerators = sum(map(lambda node_name: node_map[node_name].LogicalAccelerators,
                                           #node_names)) / len(node_names)
            accel_env.MainMemorySize = sum([node_map[node_name].MainMemorySize for node_name in node_names]) / len(node_names)
            accel_env.TotalInstances = len(node_names)
            accel_env.UsedInstances = sum([node_map[node_name].UsedInstances for node_name in node_names])
            accel_env.UnavailableInstances = sum([node_map[node_name].UnavailableInstances for node_name in node_names])
            # remove nodes that are part of a current reservation so that they aren't counted twice
            for node_name in node_names:
                try:
                    del node_map[node_name]
                except KeyError:
                    self.warning("didn't find %s in remaining nodes" % node_name)

            # don't need to publish the node names
            del accel_env.Extension["Nodes"]

        # group up nodes that aren't part of a current reservation
        self.debug("size of node map "+str(len(node_map)))
 
        #return partitions + reservations + self._groupHosts(list(node_map.values()))
        return partitions + reservations

    def _getNode(self, node_str):
        node = accelerator_environment.AcceleratorEnvironment()

        NodeName = self.params.get("NodeName","NodeName=(\S+)")
        Sockets = self.params.get("Sockets","Sockets=(\S+)")
        CPUTot = self.params.get("CPUTot","CPUTot=(\S+)")
        RealMemory = self.params.get("RealMemory","RealMemory=(\S+)") 
        Gres = self.params.get("Gres","Gres=(\S+)")
        GresUsed = self.params.get("GresUsed","GresUsed=(\S+)")
        State = self.params.get("State","State=(\S+)")

        # ID set by AcceleratorEnvironment
        m = re.search(NodeName,node_str)
        if m is not None:
            node.Name = m.group(1)
        m = re.search(Sockets,node_str)
        if m is not None:
            node.PhysicalCPUs = int(m.group(1))
        m = re.search(CPUTot,node_str)
        if m is not None:
            node.LogicalCPUs = int(m.group(1))
        m = re.search(RealMemory,node_str)  # MB
        if m is not None:
            node.MainMemorySize = int(m.group(1))
        #AcceleratorEnvironment:
        m = re.search(Gres,node_str)
        if m is not None:
            greslist=[]
            #greslist = split(":",m.group(1))
            greslist = m.group(1).split(":")
            if len(greslist) == 2:
                node.PhysicalAccelerators = int(greslist[1])
                print(node.PhysicalAccelerators)
                node.Type = ""
            elif len(greslist) == 3:
                node.PhysicalAccelerators = int(greslist[2])
                node.Type = greslist[1] 
        m = re.search(GresUsed,node_str)
        if m is not None:
            greslist=[]
            #greslist = split(":",m.group(1))
            greslist = m.group(1).split(":")
            if len(greslist) == 2:
                node.UsedAcceleratorSlots = int(greslist[1])
                node.Type = ""
            elif len(greslist) >= 3:
                endindex = greslist[2].find("(")
                if endindex == -1:
                    node.UsedAcceleratorSlots = int(greslist[2])
                else:
                    uas = greslist[2][:endindex]
                    node.UsedAcceleratorSlots = int(uas)
                node.Type = greslist[1]
                
        m = re.search(State,node_str)
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
        partition = accelerator_environment.AcceleratorEnvironment()

        PartitionName = self.params.get("PartitionName","PartitionName=(\S+)")
        TotalNodes = self.params.get("TotalNodes","TotalNodes=(\S+)")
        Nodes = self.params.get("Nodes","\sNodes=(\S+)")

        # ID set by ExecutionEnvironment
        m = re.search(PartitionName,partition_str)
        if m is not None:
            partition.Name = m.group(1)

        m = re.search(TotalNodes,partition_str)
        if m is not None and m.group(1) != "(null)":
            partition.TotalInstances = int(m.group(1))

        m = re.search(Nodes,partition_str)
        if m is not None and m.group(1) != "(null)":
            partition.Extension["Nodes"] = self._expandNames(m.group(1))

        return partition

    def _getReservation(self, rsrv_str):
        rsrv = accelerator_environment.AcceleratorEnvironment()
        rsrv.Extension["Reservation"] = True

        ReservationName = self.params.get("ReservationName","ReservationName=(\S+)")
        StartTime = self.params.get("StartTime","StartTime=(\S+)")
        EndTime = self.params.get("EndTime","EndTime=(\S+)")
        NodeCnt = self.params.get("NodeCnt","NodeCnt=(\S+)")
        Nodes = self.params.get("Nodes","Nodes=(\S+)")
        State = self.params.get("State","State=(\S+)")
        # ID set by ExecutionEnvironment
        m = re.search(ReservationName,rsrv_str)
        if m is None:
            raise StepError("didn't find 'ReservationName'")
        rsrv.Name = m.group(1)
        rsrv.ShareID = ["urn:glue2:ComputingShare:%s.%s" % (rsrv.Name,self.resource_name)]

        m = re.search(StartTime,rsrv_str)
        if m is not None:
            rsrv.Extension["StartTime"] = _getDateTime(m.group(1))
        m = re.search(EndTime,rsrv_str)
        if m is not None:
            rsrv.Extension["EndTime"] = _getDateTime(m.group(1))

        m = re.search(NodeCnt,rsrv_str)
        if m is not None:
            rsrv.Extension["RequestedInstances"] = int(m.group(1))

        m = re.search(Nodes,rsrv_str)
        if m is not None:
            if m.group(1) != "(null)":
                rsrv.Extension["Nodes"] = self._expandNames(m.group(1))

        m = re.search(State,rsrv_str)
        if m is not None:
            if m.group(1) != "ACTIVE":
                if "Nodes" in rsrv.Extension:
                    del rsrv.Extension["Nodes"]   # not active, so no nodes at the current time

        return rsrv

    def _expandNames(self, expr):
        exprs = self._splitCommas(expr)
        if len(exprs) > 1:
            return list(itertools.chain.from_iterable(list(map(self._expandNames,exprs))))
        m = re.search("^(\S+)\[(\S+)\]$",expr)
        if m is not None:
            prefix = m.group(1)
            suffixes = self._expandNames(m.group(2))
            return [prefix+suffix for suffix in suffixes]
        m = re.search("^(\d+)-(\d+)$",expr)
        if m is not None:
            # don't drop any leading 0s
            pattern = "%%0%dd" % len(m.group(1))
            return [pattern % num for num in range(int(m.group(1)),int(m.group(2))+1)]
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
