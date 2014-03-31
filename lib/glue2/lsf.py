
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
        service.Name = "LSF"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.LSF"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "LSF"
        manager.Name = "LSF"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("bjobs","the path to the LSF bjobs program (default 'bjobs')",False)

    def _run(self):
        bjobs = self.params.get("bjobs","bjobs")

        cmd = bjobs + " -a -l -u all"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("bjobs failed: "+output+"\n")

        jobStrings = output.split("------------------------------------------------------------------------------")
        for jobString in jobStrings:
            job = self._getJob(jobString)
            if includeQueue(job.Queue):
                self.activities.append(job)

        return jobList

    def _getJob(self, jobString):
        job = glue2.computing_activity.ComputingActivity()

        # put records that are multiline on one line
        jobString = re.sub("\n                     ","",jobString)

        jobString = re.sub("\r","\n",jobString)
        lines = []
        for line in jobString.split("\n"):
            if len(line) > 0:
                lines.append(line)

        # line 0 has job information
        m = re.search(r"Job\s*<\S*>",lines[0])
        if m != None:
            job.LocalIDFromManager = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find Job")
        m = re.search(r"Job Name\s*<\S*>",lines[0])
        if m != None:
            job.Name = job._betweenAngleBrackets(m.group())
        else:
            self.info("didn't find Job Name")
                
        m = re.search(r"User\s*<\S*>",lines[0])
        if m != None:
            job.LocalOwner = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find User")
            job.LocalOwner = "UNKNOWN"

        m = re.search(r"Project\s*<\S*>",lines[0])
        if m != None:
            job.UserDomain = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find Project")

        m = re.search(r"Queue\s*<\S*>",lines[0])
        if m != None:
            job.Queue = job._betweenAngleBrackets(m.group())
        else:
            self.warn("didn't find Queue in "+lines[0])

        m = re.search(r"Status\s*<\S*>",lines[0])
        currentState = None
        if m != None:
            tempStr = m.group()
            status = job._betweenAngleBrackets(tempStr)
            if status == "RUN":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
            elif status == "PEND":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_PENDING]
            elif status == "PSUSP": # job suspended by user while pending
                # ComputingShare has SuspendedJobs, so there should be a suspended state here
                job.State = [glue2.computing_activity.ComputingActivity.STATE_HELD]
            elif status == "USUSP":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_SUSPENDED]
            elif status == "DONE":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_FINISHED]
            elif status == "ZOMBI":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
            elif status == "EXIT":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
            elif status == "UNKWN":
                job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
            else:
                self.warn("found unknown status '%s'",status)
                job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
            job.State.append("lsf:"+status)
        else:
            self.warn("didn't find Status in %s",lines[0])
            job.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]

        #m = re.search(r"Command <\S*>",lines[0])
        #tempStr = m.group()
        #tempStr[9:len(tempStr)-1]

        # lines[1] has the submit time

        #submitTime = job._getDateTime(lines[1])

        #job.addStateChange(JobStateChange(WaitingJobState(),submitTime))

        # lines[1] also has the requested processors

        m = re.search(r"\d+ Processors Requested",lines[1])
        if m != None:
            tempStr = m.group()
            job.RequestedSlots = int(tempStr.split()[0])
        else:
            self.info("didn't find Processors, assuming 1")
            job.RequestedSlots = 1

        # run limit should be in lines[3], but had one case where it wasn't
        for lineNum in range(0,len(lines)):
            if lines[lineNum].find("RUNLIMIT") != -1:
                minPos = lines[lineNum+1].find("min")
                runLimitStr = lines[lineNum+1][1:minPos-1]
                wallTime = int(float(runLimitStr)) * 60
                job.RequestedTotalWallTime = wallTime * job.RequestedSlots

        # lines[6] has the start time in it, if any

        # check the lines for events and any pending reason
        for index in range(0,len(lines)):
            if lines[index].find("Submitted from") != -1:
                job.SubmissionTime = job._getDateTime(lines[index])
                job.ComputingManagerSubmissionTime = job.SubmissionTime
            elif lines[index].find("Started on") != -1:
                job.StartTime = job._getDateTime(lines[index])
                usedWallTime = time.time() - time.mktime(job.StartTime.timetuple())
                job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            elif lines[index].find("Done successfully") != -1:
                job.ComputingManagerEndTime = job._getDateTime(lines[index])
            elif lines[index].find("Exited with exit code 1") != -1:
                job.ComputingManagerEndTime = job._getDateTime(lines[index])
            if lines[index].find("PENDING REASONS:") != -1:
                if lines[index+1].find("Job's resource requirements not satisfied") != -1:
                    # pending is correct
                    pass
                elif lines[index+1].find("New job is waiting for scheduling") != -1:
                    # held is probably better
                    job.State[0] = glue2.computing_activity.ComputingActivity.STATE_HELD
                else:
                    # held is better, even though LSF calls it PEND. some examples:
                    # Job dependency condition not satisfied;
                    self.info("setting state to held for pending reason: %s",lines[index+1])
                    job.State[0] = glue2.computing_activity.ComputingActivity.STATE_HELD

        return job

    def _betweenAngleBrackets(self, aStr):
        leftPos = aStr.find("<")
        rightPos = aStr.find(">")
        return aStr[leftPos+1:rightPos]

    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # Example: Mon May 14 14:24:11:
        # Not quite sure how it handles a different year... guessing
        dayOfWeek = aStr[:3]
        month =     aStr[4:7]
        day =       int(aStr[8:10])
        hour =      int(aStr[11:13])
        minute =    int(aStr[14:16])
        second =    int(aStr[17:19])
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

#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):

    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("bqueues","the path to the LSF bqueues program (default 'bqueues')",False)

    def _run(self):
        bqueues = self.params.get("bqueues","bqueues")

        cmd = bqueues + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("bqueues failed: "+output+"\n")

        queues = []
        queueStrings = output.split("------------------------------------------------------------------------------")
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if includeQueue(self.config,queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = glue2.computing_share.ComputingShare()

        lineNumber = 0
        lines = queueString.split("\n")

        queueName = None
        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("QUEUE:"):
                queueName = lines[lineNum][7:]
                lineNumber = lineNum + 1
                break
        if queueName == None:
            raise StepError("Error: didn't find queue name in output: "+queueString)

        ComputingShare.__init__(self,sensor)

        queue.Name = queueName
        queue.MappingQueue = queue.Name

        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("  -- "):
                queue.Description = lines[lineNum][5:]
                lineNumber = lineNum + 1
                break

        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("PRIO NICE"):
                (prio,nice,status,max,jlu,jlp,jlh,njobs,pend,run,ssusp,ususp,rsv) = lines[lineNum+1].split()
                queue.Extension["Priority"] = int(prio)
                lineNumber = lineNum + 2
                break
        
        defaultLimitsStart = -1
        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("DEFAULT LIMITS:"):
                defaultLimitsStart = lineNum + 1
                lineNumber = lineNum + 1
                break

        maxLimitsStart = -1
        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("MAXIMUM LIMITS:"):
                maxLimitsStart = lineNum + 1
                lineNumber = lineNum + 1
                break

        queue.DefaultWallTime = queue.getRunLimit(lines,defaultLimitsStart,maxLimitsStart)

        queue.MaxWallTime = queue.getRunLimit(lines,maxLimitsStart,len(lines))
        (minSlots,defaultSlots,queue.MaxSlotsPerJob) = queue.getCpuLimits(lines,maxLimitsStart,len(lines))
        if minSlots != None:
            queue.Extension["MinSlotsPerJob"] = str(minSlots)
        if defaultSlots != None:
            queue.Extension["DefaultSlotsPerJob"] = str(defaultSlots)

        # this info is a little more sensitive and perhaps shouldn't be made public
        # uncomment the return below to not publish it
        #return
        
        authorizedUsers = []
        authorizedGroups = []
        for lineNum in range(lineNumber, len(lines)):
            if lines[lineNum].startswith("USERS:"):
                usersGroups = lines[lineNum][7:].split()
                for userOrGroup in usersGroups:
                    if userOrGroup.endswith("/"):
                        authorizedGroups.append(userOrGroup[:len(userOrGroup)-1])
                    else:
                        if userOrGroup == "all": # LSF has a special token 'all'
                            authorizedUsers.append("*")
                        else:
                            authorizedUsers.append(userOrGroup)
                lineNumber = lineNum + 1
                break
        if len(authorizedUsers) > 0:
            authUserStr = None
            for user in authorizedUsers:
                if authUserStr == None:
                    authUserStr = user
                else:
                    authUserStr = authUserStr + " " + user
            # lets not include this right now in case of privacy concerns
            #queue.Extension["AuthorizedUsers"] = authUserStr

        if len(authorizedGroups) > 0:
            authGroupStr = None
            for group in authorizedGroups:
                if authGroupStr == None:
                    authGroupStr = group
                else:
                    authGroupStr = authGroupStr + " " + group
            # lets not include this right now in case of privacy concerns
            #queue.Extension["AuthorizedGroups"] = authGroupStr

    def getRunLimit(self, lines, startIndex, endIndex):
        for lineNum in range(startIndex,endIndex):
            if lines[lineNum].startswith(" RUNLIMIT"):
                toks = lines[lineNum+1].split()
                if len(toks) < 2:
                    self.warn("failed to parse run limit")
                    return None
                if toks[1] != "min":
                    self.warn("don't understand time unit '" + toks[1] + "'")
                    return None
                return float(toks[0])*60
        return None


    def getCpuLimits(self, lines, startIndex, endIndex):
        # returns (min, default, max)
        for lineNum in range(startIndex,endIndex):
            if lines[lineNum].startswith(" PROCLIMIT"):
                toks = lines[lineNum+1].split()
                if len(toks) == 1:
                    return (None, None, int(toks[0]))
                if len(toks) == 2:
                    return (int(toks[0]), None, int(toks[1]))
                if len(toks) == 3:
                    return (int(toks[0]), int(toks[1]), int(toks[2]))
                return (None,None,None)
        return (None,None,None)

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):

    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("lshosts","the path to the LSF lshosts program (default 'lshosts')",False)
        self._acceptParameter("bhosts","the path to the LSF bhosts program (default 'lshosts')",False)

    def _run(self):
        lshosts = self.params.get("lshosts","lshosts")

        cmd = lshosts + " -w"
        info.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("lshosts failed: "+output)

        lshostsRecords = {}
        lines = output.split("\n")
        for index in range(1,len(lines)):
            rec = LsHostsRecord(lines[index])
            lshostsRecords[rec.hostName] = rec

        bhosts = self.params.get("bhosts","bhosts")

        cmd = bhosts + " -w"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("bhosts failed: "+output)

        bhostsRecords = {}
        lines = output.split("\n")
        for index in range(1,len(lines)):
            rec = BHostsRecord(lines[index])
            bhostsRecords[rec.hostName] = rec

        all_hosts = []
        for host in lshostsRecords.keys():
            lshost = lshostsRecords.get(host)
            bhost = bhostsRecords.get(host)
            if bhost == None:
                info.warn("no bhost record found for "+host)
                break
            all_hosts.append(self._getHost(lshost,bhost))

        hosts = []
        for host in all_hosts:
            if self._goodHost(host):
                hosts.append(host)

        return self._groupHosts(hosts)

    def _getHost(self, lshost, bhost):
        host = glue2.execution_environment.ExecutionEnvironment()

        host.Name = lshostsRecord.hostName

        host.Platform = lshostsRecord.type.lower()

        host.TotalInstances = 1
        if bhostsRecord.status == "ok":
            host.UsedInstances = 0
            host.UnavailableInstances = 0
        elif bhostsRecord.status.find("closed") >= 0:
            host.UsedInstances = 1
            host.UnavailableInstances = 0
        elif bhostsRecord.status.find("unavail") >= 0:
            host.UsedInstances = 0
            host.UnavailableInstances = 1
        elif bhostsRecord.status.find("unlicensed") >= 0:
            host.UsedInstances = 0
            host.UnavailableInstances = 1
        elif bhostsRecord.status.find("unreach") >= 0:
            host.UsedInstances = 0
            host.UnavailableInstances = 1
        else:
            self.warn("unknown status: " + bhostsRecord.status)

        toks = lshostsRecord.model.split("_")
        host.CPUVendor = toks[0]
        host.CPUModel = lshostsRecord.model
        #host.CPUVersion
        #host.CPUClockSpeed

        host.PhysicalCPUs = lshostsRecord.numCPUs
        if (bhostsRecord.maxJobSlots != None):
            host.LogicalCPUs = bhostsRecord.maxJobSlots
        else:
            if host.PhysicalCPUs == None:
                host.LogicalCPUs = None
            else:
                # this is a bit of a hack
                coresPerCPU = 1
                if host.CPUModel.find("EM64T") >= 0:
                    coresPerCPU = 2
                if host.CPUModel.find("Woodcrest") >= 0:
                    coresPerCPU = 2
                if host.CPUModel.find("Clovertown") >= 0:
                    coresPerCPU = 4
                host.LogicalCPUs = host.PhysicalCPUs * coresPerCPU

        if host.PhysicalCPUs == 1:
            if host.LogicalCPUs == 1:
                host.CPUMultiplicity = "singlecpu-singlecore"
            else:
                host.CPUMultiplicity = "singlecpu-multicore"
        else:
            if host.LogicalCPUs == 1:
                host.CPUMultiplicity = "multicpu-singlecore"
            else:
                host.CPUMultiplicity = "multicpu-multicore"

        host.CPUTimeScalingFactor = lshostsRecord.cpuFactor
        host.WallTimeScalingFactor = lshostsRecord.cpuFactor
        host.MainMemorySize = lshostsRecord.maxMemoryMB
        if lshostsRecord.maxMemoryMB != None and lshostsRecord.maxSwapMB != None:
            host.VirtualMemorySize = lshostsRecord.maxMemoryMB + lshostsRecord.maxSwapMB
        #host.ConnectivityIn
        #host.ConnectivityOut
        #host.NetworkInfo

        # assume the node has the same operating system as the node this script runs on

#######################################################################################################################

class LsHostsRecord:
    def __init__(self, line):
        #HOST_NAME                       type       model  cpuf ncpus maxmem maxswp server RESOURCES
        #admin-0-1                     X86_64 Intel_EM64T  60.0     2  3940M  4094M    Yes ()
        toks = line.split()
        self.hostName = toks[0]
        self.type = toks[1]
        self.model = toks[2]
        if toks[3] != "-":
            self.cpuFactor = float(toks[3])
        else:
            self.cpuFactor = None
        if toks[4] != "-":
            self.numCPUs = int(toks[4])
        else:
            self.numCPUs = None
        memStr = toks[5][:len(toks[5])-1]
        if len(memStr) > 0:
            self.maxMemoryMB = int(memStr)
        else:
            self.maxMemoryMB = None
        memStr = toks[6][:len(toks[6])-1]
        if len(memStr) > 0:
            self.maxSwapMB = int(memStr)
        else:
            self.maxSwapMB = None
        if toks[7] == "Yes":
            self.isServer = True
        else:
            self.isServer = False
        self.resources = toks[8]

class BHostsRecord:
    def __init__(self, line):
        #HOST_NAME          STATUS       JL/U    MAX  NJOBS    RUN  SSUSP  USUSP    RSV
        #admin-0-1          ok              -      2      0      0      0      0      0
        toks = line.split()
        self.hostName = toks[0]
        self.status = toks[1]
        self.maxSlotsPerUser = None
        self.maxJobSlots = None
        self.jobSlotsUsed = None
        self.jobSlotsUsedByRunning = None
        self.jobSlotsUsedBySystemSuspended = None
        self.jobSlotsUsedByUserSuspended = None
        self.jobSlotsUsedByPending = None

        if len(toks) < 3:
            return

        if toks[2] != "-":
            self.maxSlotsPerUser = int(toks[2])
        if toks[3] != "-":
            self.maxJobSlots = int(toks[3])
        self.jobSlotsUsed = int(toks[4])
        self.jobSlotsUsedByRunning = int(toks[5])
        self.jobSlotsUsedBySystemSuspended = int(toks[6])
        self.jobSlotsUsedByUserSuspended = int(toks[7])
        self.jobSlotsUsedByPending = int(toks[8])

#######################################################################################################################
