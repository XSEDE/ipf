
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

from ipf.error import StepError

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
        service.Name = "Condor"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.Condor"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "Condor"
        manager.Name = "Condor"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):
    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("condor_q","the path to the Condor condor_q program (default 'condor_q')",False)

    def _run(self):
        condor_q = self.params.get("condor_q","condor_q")

        cmd = condor_q + " -long"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("condor_q failed: "+output+"\n")

        jobStrings = output.split("\n\n")

        jobs = []
        for jobString in jobStrings:
            job = self._getJob(jobString)
            if job != None and includeQueue(self.config,job.Queue,True):
                jobs.append(job)

        for job in jobs:
            job.id = job.LocalIDFromManager+"."+self._getSystemName()

        return jobs

    def _getJob(self, jobString):
        job = glue2.computing_activity.ComputingActivity()

        # put multi-lines on one line?

        clusterId = None
        procId = None
        usedWallTime = None
        usedCpuTime = None
	lines = jobString.split("\n")
	for line in lines:
            if line.startswith("ClusterId = "):
                clusterId = line.split()[2]
            if line.startswith("ProcId = "):
                procId = line.split()[2]
            # don't think there are any job.Name...
            if line.startswith("Owner = "):
                owner = line.split()[2]
                job.LocalOwner =  owner[1:len(owner)-1]
            if line.startswith("TGProject = "):
                project = line.split()[2]
                job.UserDomain = project[1:len(project)-1]
            # job.Queue doesn't apply
            if line.startswith("JobStatus = "):
                status = line.split()[2]
                if status == "0":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING,
                                 "htcondor:Unexpanded"]
                elif status == "1":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING,
                                 "htcondor:Idle"]
                elif status == "2":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING,
                                 "htcondor:Running"]
                elif status == "3":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED,
                                 "htcondor:Removed"]
                elif status == "4":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED,
                                 "htcondor:Completed"]
                elif status == "5":
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_HELD,
                                 "htcondor:Held"]
                elif status == "6":
                    job.State = [glue2.computing_activity.ComputingActivity.FAILED,
                                 "htcondor:Submission_err"]
                elif status == "7":
                    job.State = [glue2.computing_activity.ComputingActivity.SUSPENDED,
                                 "htcondor:Suspended"]
                else:
                    self.warning("found unknown Condor job status '" + status + "'")
                    job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]

            # not sure if this is right - don't see any mpi jobs for comparison
            if line.startswith("MinHosts = "):
                job.RequestedSlots = int(line.split()[2])
                if usedWallTime != None:
                    job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
                if usedCpuTime != None:
                    job.UsedTotalCpuTime = usedCpuTime * job.RequestedSlots

            # job.RequestedTotalWallTime doesn't apply

            if line.startswith("RemoteWallClockTime = "):
                if float(line.split()[2]) > 0:
                    usedWallTime = float(line.split()[2])
                    if job.RequestedSlots != None:
                        job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            if line.startswith("RemoteUserCpu = "):
                if float(line.split()[2]) > 0:
                    usedCpuTime = float(line.split()[2])
                    if job.RequestedSlots != None:
                        job.UsedTotalCpuTime = usedCpuTime * job.RequestedSlots

            if line.startswith("QDate = "):
                job.SubmissionTime = self._getDateTime(line.split()[2])
                job.ComputingManagerSubmissionTime = job.SubmissionTime
            if line.startswith("JobStartDate = "):
                job.StartTime = self._getDateTime(line.split()[2])
            if line.startswith("CompletionDate = "):
                date = line.split()[2]
                if date != "0":
                    job.ComputingManagerEndTime = self._getDateTime(date)

        if clusterId == None or procId == None:
            self.error("didn't find cluster or process ID in " + jobString)
            return None

        job.LocalIDFromManager = clusterId+"."+procId

        return job

    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # string containing the epoch time
        return datetime.datetime.fromtimestamp(float(aStr),localtzoffset())

#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):

    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("qstat","the path to the PBS qstat program (default 'qstat')",False)

    def _run(self):
        return []

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):

    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("condor_status",
                              "the path to the Condor condor_status program (default 'condor_status')",
                              False)

    def _run(self):
        condor_status = self.params.get("condor_status","condor_status")

        cmd = condor_status + " -long"
        info.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("condor_status failed: "+output+"\n")

        node_strings = output.split("\n\n")

        hosts = []
        for node_string in node_strings:
            host = self._getHost(node_string)
            if self._goodHost(host):
                hosts.append(host)

        return self._groupHosts(hosts)

    def _getHost(self, node_str):
        host = glue2.execution_environment.ExecutionEnvironment()

        load = None
        lines = node_str.split("\n")
        # ID set by ExecutionEnvironment
        for line in lines:
            if line.startswith("Name = "):
                host.Name = line.split()[2]
                host.Name = host.Name[1:len(host.Name)-1]
            if line.startswith("State = "):
                state = line.split()[2]
                state = state[1:len(state)-1]
                if state == "Owner":
                    host.UsedInstances = 0
                    host.UnavailableInstances = 1
                elif state == "Unclaimed":
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                elif state == "Matched":
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif state == "Claimed":
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif state == "Preempting":
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                else:
                    logger.warn("unknown state: "+state)
                    host.UsedInstances = 0
                    host.UnavailableInstances = 1
                host.TotalInstances = 1
                if load != None:
                    if host.UsedInstances > 0:
                        host.Extension["UsedAverageLoad"] = load
                    elif host.UnavailableInstances == 0:
                        host.Extension["AvailableAverageLoad"] = load
            if line.startswith("LoadAvg = "):
                load = float(line.split()[2])
                if host.TotalInstances != None:
                    if host.UsedInstances > 0:
                        host.Extension["UsedAverageLoad"] = load
                    elif host.UnavailableInstances == 0:
                        host.Extension["AvailableAverageLoad"] = load
            if line.startswith("Cpus = "):
                host.PhysicalCPUs = int(line.split()[2])
                host.LogicalCPUs = host.PhysicalCPUs
            if line.startswith("Memory = "):
                host.MainMemorySize = int(line.split()[2]) # assuming MB
            if line.startswith("VirtualMemory = "):
                memSize = line.split()[2]
                if memSize != "0":
                    host.VirtualMemorySize = int(memSize) # assuming MB
            if line.startswith("OpSys = "):
                host.OSFamily = line.split()[2].lower()
                host.OSFamily = host.OSFamily[1:len(host.OSFamily)-1]
            if line.startswith("Arch = "):
                host.Platform = line.split()[2].lower()
                host.Platform = host.Platform[1:len(host.Platform)-1]
            if line.startswith("CheckpointPlatform = "):
                host.OSVersion = line.split()[4]

        return host
        
#######################################################################################################################
