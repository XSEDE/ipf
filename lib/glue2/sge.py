
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
import time
import xml.sax
import xml.sax.handler

from ipf.dt import *
from ipf.error import StepError

import glue2.computing_activity
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
import glue2.execution_environment
from glue2.log import LogFileWatcher

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

        # the output of -u is in schedule order
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
        # dom parsing was slow
        # sax parsing failed sometimes
        parseJLines(output,jobs,self)

        jobList = []
        for job in uhandler.jobs:
            if self._includeQueue(job.Queue):
                jobList.append(job)

        return jobList

#######################################################################################################################

class JobsUHandler(xml.sax.handler.ContentHandler):

    def __init__(self, step):
        self.step = step
        self.cur_job = None
        self.jobs = []
        self.cur_time = time.time()
        
        self.text = ""

    def startDocument(self):
        pass

    def endDocument(self):
        if self.cur_job is not None:
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
            if self.cur_job is not None:
                self.jobs.append(self.cur_job)
            self.cur_job = glue2.computing_activity.ComputingActivity()
            self.cur_job.LocalIDFromManager = self.text
        if name == "state":
            if self.text == "r":
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            elif self.text == "R": # restarted
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            elif self.text.find("d") >= 0: # deleted
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_TERMINATED
            elif self.text.find("E") >= 0: # error - Eqw
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_FAILED
            elif self.text.find("h") >= 0: # held - hqw, hr
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_HELD
            elif self.text.find("w") >= 0: # waiting - qw
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            elif self.text == "t": # transfering
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_PENDING
            else:
                self.step.warning("found unknown SGE job state '" + self.text + "'")
                self.cur_job.State = glue2.computing_activity.ComputingActivity.STATE_UNKNOWN
        if name == "JAT_start_time":
            self.cur_job.StartTime = _getDateTime(self.text)         
        # JAT_submission_time isn't provided for running jobs, so just get it from -j

    def characters(self, ch):
        # all of the text for an element may not come at once
        self.text = self.text + ch
        
#######################################################################################################################

def parseJLines(output, jobs, step):
    cur_time = time.time()

    job_strings = []
    index = output.find("<JB_job_number>")
    while index >= 0:
        next_index = output.find("<JB_job_number>",index+1)
        if next_index == -1:
            job_strings.append(output[index:])
        else:
            job_strings.append(output[index:next_index])
        index = next_index

    cur_job = None
    for job_string in job_strings:
        m = re.search("<JB_job_number>(\S+)</JB_job_number>",job_string)
        if m is not None:
            cur_job = jobs.get(m.group(1))
        else:
            continue
        m = re.search("<JB_job_name>(\S+)</JB_job_name>",job_string)
        if m is not None:
            cur_job.Name = m.group(1)
        m = re.search("<JB_owner>(\S+)</JB_owner>",job_string)
        if m is not None:
            cur_job.LocalOwner = m.group(1)
        m = re.search("<JB_account>(\S+)</JB_account>",job_string)
        if m is not None:
            cur_job.UserDomain = m.group(1)
        m = re.search("<QR_name>(\S+)</QR_name>",job_string)
        if m is not None:
            cur_job.Queue = m.group(1)
            # below needs to match how ID is calculated in the ComputingShareAgent
            cur_job.ComputingShare = ["http://"+step.resource_name+"/glue2/ComputingShare/"+cur_job.Queue]
        m = re.search("<JB_submission_time>(\S+)</JB_submission_time>",job_string)
        if m is not None:
            cur_job.ComputingManagerSubmissionTime = epochToDateTime(int(m.group(1)),localtzoffset())
        else:
            step.warning("didn't find submission time in %s",job_string)
        m = re.search("<JB_pe_range>([\s\S]+)</JB_pe_range>",job_string)
        if m is not None:
            m = re.search("<RN_min>(\S+)</RN_min>",m.group(1))
            if m is not None:
                cur_job.RequestedSlots = int(m.group(1))
        lstrings = re.findall("<qstat_l_requests>[\s\S]+?</qstat_l_requests>",job_string)
        for str in lstrings:
            if "h_rt" in str:
                m = re.search("<CE_doubleval>(\S+)</CE_doubleval>",job_string)
                if m is not None:
                    cur_job.RequestedTotalWallTime = cur_job.RequestedSlots * int(float(m.group(1)))
        # start time isn't often in the -j output, so get it from -u
        if cur_job.StartTime is not None:
            usedWallTime = int(cur_time - time.mktime(cur_job.StartTime.timetuple()))
            cur_job.UsedTotalWallTime = usedWallTime * cur_job.RequestedSlots

        # looks like PET_end_time isn't ever valid
        sstrings = re.findall("<scaled>[\s\S]+?</scaled>",job_string)
        for str in sstrings:
            m = re.search("<UA_value>(\S+)</UA_value>",str)
            if m is None:
                continue
            if "<UA_name>end_time</UA_name>" in str:
                if int(float(m.group(1))) > 0:
                    cur_job.ComputingManagerEndTime = epochToDateTime(float(m.group(1)),localtzoffset())
            if "<UA_name>exit_status</UA_name>" in str:
                cur_job.ComputingManagerExitCode = int(float(m.group(1)))

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
        self._acceptParameter("qstat","the path to the SGE qstat program (default 'qstat')",False)

        self.activities = {}

    def _run(self):
        self.info("running")

        # if a site is generating a schedd_runlog, can use it to find jobs that are held because of dependencies

        try:
            reporting_filename = self.params["reporting_file"]
        except KeyError:
            try:
                reporting_filename = os.path.join(os.environ["SGE_ROOT"],"default","common","reporting")
            except KeyError:
                msg = "no reporting_file specified and the SGE_ROOT environment variable is not set"
                self.error(msg)
                raise StepError(msg)
        watcher = LogFileWatcher(self._logEntry,reporting_filename)
        watcher.run()

    def _logEntry(self, log_file_name, line):
        if line.startswith("#"):
            return

        toks = line.split(":")

        if toks[1] == "new_job":
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

        if toks[4] in self.activities:
            activity = self.activities[toks[4]]
        else:
            activity = glue2.computing_activity.ComputingActivity()

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
            self.activities[activity.LocalIDFromManager] = activity
        elif toks[3] == "sent":
            # sent to execd - just ignore
            return
        elif toks[3] == "delivered":
            # job received by execd - job started
            activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            activity.StartTime = event_dt
        elif toks[3] == "finished":
            if activity.ComputingManagerEndTime is not None:
                # could be a finished message after an error - ignore it
                return
            activity.State = glue2.computing_activity.ComputingActivity.STATE_FINISHED
            activity.ComputingManagerEndTime = event_dt
            if activity.LocalIDFromManager in self.activities:
                del self.activities[activity.LocalIDFromManager]
        elif toks[3] == "deleted":
            # scheduler deleting the job and a finished appears first, so ignore
            return
        elif toks[3] == "error":
            activity.State = glue2.computing_activity.ComputingActivity.STATE_FAILED
            activity.ComputingManagerEndTime = event_dt
            if activity.LocalIDFromManager in self.activities:
                del self.activities[activity.LocalIDFromManager]
        elif toks[3] == "restart":
            # restart doesn't seem to mean that the job starts running again
            # restarts occur after errors (an attempt to restart?) - just ignore them
            return
            #activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
            #activity.StartTime = event_dt
        else:
            self.warning("unknown job log of type %s" % toks[3])

        # these records are missing a few things, like the # nodes
        if activity.RequestedSlots is None:
            self.addInfo(activity)
        
        if self._includeQueue(activity.Queue):
            self.output(activity)

    def addInfo(self, job):
        try:
            qstat = self.params["qstat"]
        except KeyError:
            qstat = "qstat"
        cmd = qstat + " -xml -s prsz -j " + job.LocalIDFromManager
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("qstat failed: "+output+"\n")
        parseJLines(output,{job.LocalIDFromManager: job},self)

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
        queue = glue2.computing_share.ComputingShare()

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
                    try:
                        queue.MaxMainMemory = int(value)
                    except ValueError:
                        # may have a unit on the end
                        unit = value[len(value-1):]
                        queue.MaxMainMemory = int(value[:len(value-1)])
                        if unit == "K":
                            queue.MaxMainMemory /= 1024
                        if unit == "G":
                            queue.MaxMainMemory *= 1024
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
        if self.cur_host is not None and self._goodHost(self.cur_host):
            self.hosts.append(self.cur_host)

    def startElement(self, name, attrs):
        if name == "host":
            self.cur_host = glue2.execution_environment.ExecutionEnvironment()
            self.cur_host.Name = attrs.getValue("name")
            self.cur_host.TotalInstances = 1
            self.cur_host.ComputingManager = "http://"+self.step.resource_name+"/glue2/ComputingManager"
        elif name == "queue":
            self.cur_host.ComputingShare.append(attrs.getValue("name")) # LocalID
        elif name == "hostvalue":
            self.hostvalue_name = attrs.getValue("name")
        
    def endElement(self, name):
        if name == "host":
            if self.cur_host.PhysicalCPUs is not None:
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
