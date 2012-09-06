
###############################################################################
#   Copyright 2011-2012 The University of Texas at Austin                     #
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
import xml.sax
import xml.sax.handler

from ipf.error import StepError

import glue2.computing_activity
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
import glue2.execution_environment
from glue2.teragrid.platform import PlatformMixIn

#######################################################################################################################

class ComputingServiceStep(glue2.computing_service.ComputingServiceStep):

    def __init__(self):
        glue2.computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = glue2.computing_service.ComputingService()
        service.Name = "SGE"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager",
                              "executionmanagement.executionandplanning",
                              "executionmanagement.reservation",
                              ]
        service.Type = "org.teragrid.SGE"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):

    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "SGE"
        manager.Name = "SGE"
        manager.Reservation = True
        #self.BulkSubmission = True

        return manager

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("qstat","the path to the SGE qstat program (default 'qstat')",False)

    def _run(self):
        try:
            qstat = self.params["qstat"]
        except KeyError:
            qstat = "qstat"

        cmd = qstat + " -xml -pri -s prsz -u \\*"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qstat failed: "+output+"\n")
            raise StepError("qstat failed: "+output+"\n")

        uhandler = JobsUHandler(self)
        xml.sax.parseString(output,uhandler)

        jobs = {}
        for job in uhandler.jobs:
            jobs[job.LocalIDFromManager] = job

        cmd = qstat + " -xml -s prsz -j \\*"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qstat failed: "+output+"\n")
            raise StepError("qstat failed: "+output+"\n")

        jhandler = JobsJHandler(self,jobs)
        try:
            xml.sax.parseString(output,jhandler)
        except xml.sax.SAXParseException, e:
            # sax parsing fails sometimes
            self.warning("parsing of XML output from qstat -j failed, parsing line by line instead")
            self.parseJLines(output,jobs)

        jobList = []
        for job in uhandler.jobs:
            if self._includeQueue(job.Queue):
                jobList.append(job)

        return jobList

    def parseJLines(self, output, jobs):
        H_RT = 1
        MEM_TOTAL = 2
        cur_resource = None

        ua_name = None
        cur_job = None
        for line in output.splitlines():
            m = re.search("<JB_job_number>(\S+)</JB_job_number>",line)
            if m != None:
                cur_job = jobs.get(m.group(1))
                continue
            if cur_job == None:
                continue
            m = re.search("<JB_account>(\S+)</JB_account>",line)
            if m != None:
                cur_job.UserDomain = m.group(1)
                continue
            m = re.search("<JB_project>(\S+)</JB_project>",line)
            if m != None:
                cur_job.Queue = m.group(1)
                # below needs to match how ID is calculated in the ComputingShareAgent
                cur_job.ComputingShare = ["http://"+self.resource_name+"/glue2/ComputingShare/"+cur_job.Queue]
                continue
            m = re.search("<CE_name>(\S+)</CE_name>",line)
            if m != None:
                if m.group(1) == "h_rt":
                    cur_resource = H_RT
                elif m.group(1) == "mem_total":
                    cur_resource = MEM_TOTAL
                continue
            m = re.search("<CE_doubleval>(\S+)</CE_doubleval>",line)
            if m != None:
                if cur_resource == H_RT:
                    cur_job.RequestedTotalWallTime = cur_job.RequestedSlots * int(float(m.group(1)))
                elif cur_resource == MEM_TOTAL:
                    pass
                continue
            m = re.search("<JB_submission_time>(\S+)</JB_submission_time>",line)
            if m != None:
                cur_job.ComputingManagerSubmissionTime = epochToDateTime(int(m.group(1)),localtzoffset())
                continue
            m = re.search("<UA_name>(\S+)</UA_name>",line)
            if m != None:
                ua_name = m.group(1)
                continue
            m = re.search("<UA_value>(\S+)</UA_value>",line)
            if m != None:
                if ua_name == "exit_status":
                    cur_job.ComputingManagerExitCode = int(float(m.group(1)))
                elif ua_name == "start_time":
                    cur_job.StartTime = epochToDateTime(float(m.group(1)),localtzoffset())
                elif ua_name == "end_time":
                    cur_job.ComputingManagerEndTime = epochToDateTime(float(m.group(1)),localtzoffset())

#######################################################################################################################

        # this indicates that SGE should reserve resources for this job (and sorta backfill around it)
        #if line.startswith("reserve:"):
        #if line.split()[1] == "y":
        #self.Extension["SgeReserve"] = "yes"

#######################################################################################################################

class JobsUHandler(xml.sax.handler.ContentHandler):

    # get submission time from qstat -j

    def __init__(self, step):
        self.step = step
        self.cur_job = None
        self.jobs = []
        self.cur_time = time.time()
        
        self.text = ""

    def startDocument(self):
        pass

    def endDocument(self):
        if self.cur_job != None:
            self.jobs.append(self.cur_job)

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        self._handleElement(name)
        # get ready for next element
        self.text = ""

    def _handleElement(self, name):
        # get rid of whitespace on either side
        self.text = self.text.lstrip().rstrip()

        if name == "JB_job_number":
            if self.cur_job != None:
                self.jobs.append(self.cur_job)
            self.cur_job = glue2.computing_activity.ComputingActivity()
            self.cur_job.LocalIDFromManager = self.text
        elif name == "JAT_prio":
            self.priority = float(self.text)
        elif name == "JB_name":
            self.cur_job.Name = self.text
        elif name == "JB_owner":
            self.cur_job.LocalOwner = self.text
        elif name == "state":
            if self.text == "r":
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            elif self.text == "R": # restarted
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            elif self.text.find("d") >= 0: # deleted
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_TERMINATED
            elif self.text.find("h") >= 0: # held - hqw, hr
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_HELD
            elif self.text.find("E") >= 0: # waiting - Eqw
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_FAILED
            elif self.text.find("w") >= 0: # waiting - qw
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            elif self.text == "t": # transfering
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            else:
                self.step.warning("found unknown SGE job state '" + self.text + "'")
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_UNKNOWN
        elif name == "slots":
            self.cur_job.RequestedSlots = int(self.text)
            if self.cur_job.StartTime != None:
                usedWallTime = int(self.cur_time - time.mktime(self.cur_job.StartTime.timetuple()))
                self.cur_job.UsedTotalWallTime = usedWallTime * self.cur_job.RequestedSlots

        # also in -j output
        #elif name == "JAT_start_time":
        #    self.cur_job.StartTime = _getDateTime(self.text)

    def characters(self, ch):
        # all of the text for an element may not come at once
        self.text = self.text + ch
        
#######################################################################################################################

class JobsJHandler(xml.sax.handler.ContentHandler):

    RESOURCE_MEM_TOTAL = 1
    RESOURCE_H_RT = 2

    def __init__(self, step, jobs):
        self.step = step
        self.jobs = jobs
        self.cur_resource = None
        self.cur_job = None
        self.text = ""

        self.ua_name = None
        
    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def startElement(self, name, attrs):
        pass
    
    def endElement(self, name):
        self._handleElement(name)
        # get ready for next element
        self.text = ""

    def _handleElement(self, name):
        # get rid of whitespace on either side
        self.text = self.text.lstrip().rstrip()

        if name == "JB_job_number":
            self.cur_job = self.jobs.get(self.text)
        if self.cur_job == None: # everything else needs a current job
            return
        if name == "JB_account":
            self.cur_job.UserDomain = self.text
        if name == "JB_project":
            self.cur_job.Queue = self.text
        if name == "CE_name":
            if self.text == "h_rt":
                self.cur_resource = JobsJHandler.RESOURCE_H_RT
            elif self.text == "mem_total":
                self.cur_resource = JobsJHandler.RESOURCE_MEM_TOTAL
            else:
                self.cur_resource = None
        if name == "CE_doubleval":
            if self.cur_resource == JobsJHandler.RESOURCE_H_RT:
                self.cur_job.RequestedTotalWallTime = self.cur_job.RequestedSlots * int(float(self.text))
            if self.cur_resource == JobsJHandler.RESOURCE_MEM_TOTAL:
                pass
        if name == "JB_submission_time":
            self.cur_job.ComputingManagerSubmissionTime = epochToDateTime(int(self.text),localtzoffset())
        if name == "UA_name":
            self.ua_name = self.text
        if name == "UA_value":
            if self.ua_name == "exit_status":
                self.cur_job.ComputingManagerExitCode = int(float(self.text))
            if self.ua_name == "start_time":
                self.cur_job.StartTime = epochToDateTime(float(self.text),localtzoffset())
            if self.ua_name == "end_time":
                self.cur_job.ComputingManagerEndTime = epochToDateTime(float(self.text),localtzoffset())

    def characters(self, ch):
        self.text = self.text + ch

#######################################################################################################################

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

        self._acceptParameter("reporting_file","the path to the SGE reporting file (optional)",False)

    def _run(self):
        self.info("running")

        try:
            reporting_filename = self.params["reporting_file"]
        except KeyError:
            try:
                reporting_filename = os.path.join(os.environ["SGE_ROOT"],"default","common","reporting")
            except KeyError:
                msg = "no reporting_file specified and the SGE_ROOT environment variable is not set"
                self.error(msg)
                raise StepError(msg)

        try:
            file = open(reporting_filename,"r")
        except IOError:
            msg = "could not open SGE reporting file %s" % reporting_filename
            self.error(msg)
            raise StepError(msg)

        # if a site is generating a schedd_runlog, can use it to find jobs that are held because of dependencies

        file.seek(0,2)
        while True:
            where = file.tell()
            line = file.readline()
            if not line:
                time.sleep(1)
                file.seek(where)
            else:
                self.handleEntry(line)

    def handleEntry(self, line):
        if line.startswith("#"):
            return

        toks = line.split(":")

        if toks[1] == "new_job":
            #self.handleNewJob(toks)
            pass # there is a job_log for every new job, so ignore these
        elif toks[1] == "job_log":
            self.handleJobLog(toks)
        elif toks[1] == "queue":
            pass # ignore
        elif toks[1] == "acct":
            # accounting records have job configuration information, but are generated when the job completes
            pass
        else:
            self.info("unknown type: %s" % toks[1])

    def handleNewJob(self, toks):
        # log time
        # new_job
        # submit time
        # job id
        # dunno (always -1)
        # dunno (always NONE)
        # job name?
        # user name
        # group name
        # queue
        # department (ignore)
        # charge account
        # dunno (always 1024)

        activity = glue2.computing_activity.ComputingActivity()
        activity.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
        activity.ComputingManagerSubmissionTime = datetime.datetime.fromtimestamp(float(toks[2]),tzoffset(0))
        activity.LocalIDFromManager = toks[3]
        activity.Name = toks[6]
        activity.LocalOwner = toks[7]
        # ignore group
        activity.Queue = toks[9]
        activity.ComputingShare = ["http://"+self.resource_name+"/glue2/ComputingShare/"+activity.Queue]
        activity.UserDomain = toks[11]

        if self._includeQueue(activity.Queue):
            self.output(activity)

#1329699034:new_job:1329699034:2373873:-1:NONE:myjob:hx634:G-800513:development:defaultdepartment:TACC-PCSE:1024

#1329699147:job_log:1329699147:sent:2373873:0:NONE:t:master:sge2.ranger.tacc.utexas.edu:0:1024:1329699034:myjob:hx634:G-800513:development:defaultdepartment:TACC-PCSE:sent to execd

#1338574037:job_log:1338574037:finished:2599414:0:NONE:r:master:sge2.ranger.tacc.utexas.edu:0:1024:1338573943:schmIin_de:mthapa01:G-800583:development:defaultdepartment:LES_Liu_Lu_UTA:job waits for schedds deletion


    def handleJobLog(self, toks):
        # log time
        # job_log
        # event time ?
        # type
        # job id
        # dunno (always 0)
        # dunno (always NONE)
        # dunno (r, t, T ...)
        # source? (master, execution daemon, scheduler)
        # dunno (sge2.ranger.tacc.utexas.edu)
        # dunno (0)
        # dunno (always 1024)
        # time of some kind
        # job name?
        # user name
        # group name
        # queue
        # department (ignore)
        # charge account
        # comment

        if len(toks) != 20:
            logger.warning("Expected 20 tokens in log entry, but found %d. Ignoring." % len(toks))
            return

        if toks[8] == "execution daemon":
            # these are redundant to what master logs, so ignore
            return

        activity = sge.computing_activity.ComputingActivity()

        event_dt = datetime.datetime.fromtimestamp(float(toks[2]),tzoffset(0))
        activity.LocalIDFromManager = toks[4]
        activity.Name = toks[13]
        activity.LocalOwner = toks[14]
        # ignore group
        activity.Queue = toks[16]
        activity.ComputingShare = ["http://"+self.resource_name+"/glue2/ComputingShare/"+activity.Queue]
        activity.UserDomain = toks[18]

        if toks[3] == "pending":
            activity.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            activity.ComputingManagerSubmissionTime = event_dt
        elif toks[3] == "sent":
            # sent to execd - just ignore
            return
        elif toks[3] == "delivered":
            # job received by execd - job started
            activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            activity.StartTime = event_dt
        elif toks[3] == "finished":
            activity.State = glue2.computing_activity.ComputingActivity.STATE_FINISHED
            activity.ComputingManagerEndTime = event_dt
        elif toks[3] == "deleted":
            # scheduler deleting the job and a finished appears first, so ignore
            return
        elif toks[3] == "error":
            self.info("ignoring error state for job %s" % activity.LocalIDFromManager)
            return
        elif toks[3] == "restart":
            activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            activity.StartTime = event_dt
        else:
            self.warning("unknown job log of type %s" % toks[3])

        if self._includeQueue(activity.Queue):
            self.output(activity)

#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):

    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

        self._acceptParameter("qconf","the path to the SGE qconf program (default 'qconf')",False)

    def _run(self):
        try:
            qconf = self.params["qconf"]
        except KeyError:
            qconf = "qconf"
        cmd = qconf + " -sq \**"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qconf failed: "+output+"\n")
            raise StepError("qconf failed: "+output+"\n")

        queues = []
        queueStrings = output.split("\n\n")
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if self._includeQueue(queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()

        lines = queueString.split("\n")
        queueName = None
        for line in lines:
            if line.startswith("qname "):
                queueName = line[5:].lstrip()
                break

        queue.Name = queueName
        queue.MappingQueue = queue.Name

        for line in lines:
            if line.startswith("s_rt "):
                value = line[4:].lstrip()
                if value != "INFINITY":
                    queue.MaxWallTime = self._getDuration(value)
            if line.startswith("s_cpu "):
                value = line[5:].lstrip()
                if value != "INFINITY":
                    queue.MaxTotalCPUTime = self._getDuration(value)
            if line.startswith("h_data "):
                value = line[6:].lstrip()
                if value != "INFINITY":
                    queue.MaxMemory = self._getDuration(value)
        return queue
    
    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):

    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("qhost","the path to the SGE qhost program (default 'qhost')",False)

    def _run(self):
        try:
            qhost = self.params["qhost"]
        except KeyError:
            qhost = "qhost"

        cmd = qhost + " -xml -q"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qhost failed: "+output+"\n")
            raise StepError("qhost failed: "+output+"\n")

        handler = HostsHandler(self)
        xml.sax.parseString(output,handler)

        hosts = []
        for host in handler.hosts:
            if self._goodHost(host):
                hosts.append(host)

        return hosts

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

class HostsHandler(xml.sax.handler.ContentHandler):

    def __init__(self, step):
        self.step = step
        self.cur_host = None
        self.hosts = []
        self.cur_time = time.time()
        self.hostvalue_name = None
        self.text = ""

    def startDocument(self):
        pass

    def endDocument(self):
        if self.cur_host != None and self._goodHost(self.cur_host):
            self.hosts.append(self.cur_host)

    def startElement(self, name, attrs):
        if name == "host":
            self.cur_host = ExecutionEnvironment()
            self.cur_host.Name = attrs.getValue("name")
            self.cur_host.TotalInstances = 1
            self.cur_host.ComputingManager = "http://"+self.step.resource_name+"/glue2/ComputingManager"
        elif name == "queue":
            self.cur_host.ComputingShare.append(attrs.getValue("name")) # LocalID
        elif name == "hostvalue":
            self.hostvalue_name = attrs.getValue("name")
        
    def endElement(self, name):
        if name == "host":
            if self.cur_host.PhysicalCPUs != None:
                self.hosts.append(self.cur_host)
            self.cur_host = None

        self.text = self.text.lstrip().rstrip()
        if name == "hostvalue":
            if self.hostvalue_name == "arch_string":
                # SGE does some unknown crazy stuff to get their arch string. Just use the defaults.
                pass
            elif self.hostvalue_name == "num_proc":
                if self.text != "-":
                    self.cur_host.PhysicalCPUs = int(self.text)
                    self.cur_host.LogicalCPUs = self.cur_host.PhysicalCPUs  # don't have enough info for something else
            elif self.hostvalue_name == "load_avg":
                if self.text == "-":
                    self.cur_host.UsedInstances = 0
                    self.cur_host.UnavailableInstances = 1
                else:
                    load = float(self.text)
                    if load > float(self.cur_host.PhysicalCPUs)/2:
                        self.cur_host.Extension["UsedAverageLoad"] = load
                        self.cur_host.UsedInstances = 1
                        self.cur_host.UnavailableInstances = 0
                    else:
                        self.cur_host.Extension["AvailableAverageLoad"] = load
                        self.cur_host.UsedInstances = 0
                        self.cur_host.UnavailableInstances = 0
            elif self.hostvalue_name == "mem_total":
                if self.text != "-":
                    units = self.text[len(self.text)-1:]    # 'M' or 'G'
                    memSize = float(self.text[:len(self.text)-1])
                    if units == "G":
                        self.cur_host.MainMemorySize = int(memSize * 1024)
                    elif units == "M":
                        self.cur_host.MainMemorySize = int(memSize)
                    else:
                        self.step.warning("couldn't handle memory units of '"+units+"'")
            elif self.hostvalue_name == "mem_used":
                pass
            elif self.hostvalue_name == "swap_total":
                pass
            elif self.hostvalue_name == "swap_used":
                pass
            self.hostvalue_name = None
        self.text = ""

    def characters(self, ch):
        # all of the text for an element may not come at once
        self.text = self.text + ch
        
#######################################################################################################################
