#!/usr/bin/env python

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
import copy
import datetime
import re
import xml.sax
import xml.sax.handler

from ipf.error import StepError

from glue2.computing_activity import *

##############################################################################################################

class SgeComputingActivitiesStep(ComputingActivitiesStep):
    name = "glue2/sge/computing_activities"
    accepts_params = copy.copy(ComputingActivitiesStep.accepts_params)
    accepts_params["qstat"] = "the path to the SGE qstat program (default 'qstat')"

    def __init__(self, params):
        ComputingActivitiesStep.__init__(self,params)

    def _run(self):
        self.info("running")

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

        for job in jobList:
            job.id = job.LocalIDFromManager+"."+self.resource_name

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

##############################################################################################################

        # this indicates that SGE should reserve resources for this job (and sorta backfill around it)
        #if line.startswith("reserve:"):
        #if line.split()[1] == "y":
        #self.Extension["SgeReserve"] = "yes"

##############################################################################################################

class JobsUHandler(xml.sax.handler.ContentHandler):

    # get submission time from qstat -j

    def __init__(self, step):
        self.step = step
        self.cur_job = None
        self.jobs = []
        self.cur_time = time.time()
        self.state = None
        
        self.text = ""

    def startDocument(self):
        pass

    def endDocument(self):
        if self.cur_job != None:
            self.jobs.append(self.cur_job)

    def startElement(self, name, attrs):
        if name == "job_list":
            self.state = attrs["state"]

    def endElement(self, name):
        self._handleElement(name)
        self.state = None
        # get ready for next element
        self.text = ""

    def _handleElement(self, name):
        # get rid of whitespace on either side
        self.text = self.text.lstrip().rstrip()

        if name == "JB_job_number":
            if self.cur_job != None:
                self.jobs.append(self.cur_job)
            self.cur_job = ComputingActivity()
            self.cur_job.LocalIDFromManager = self.text
            if self.state == "running":
                self.cur_job.State = "teragrid:running"
            elif self.state == "pending":
                self.cur_job.State = "teragrid:pending"
            elif self.state == "zombie":
                self.cur_job.State = "teragrid:pending"
            else:
                self.step.warning("unknown job state %s" % self.state)
        elif name == "JAT_prio":
            self.priority = float(self.text)
        elif name == "JB_name":
            self.cur_job.Name = self.text
        elif name == "JB_owner":
            self.cur_job.LocalOwner = self.text
        elif name == "state":
            pass # switching to above
            if self.text == "r":
                self.cur_job.State = "teragrid:running"
            elif self.text == "R": # restarted
                self.cur_job.State = "teragrid:running"
            elif self.text.find("d") >= 0: # deleted
                self.cur_job.State = "teragrid:terminated"
            elif self.text.find("w") >= 0: # waiting - qw, Eqw, hqw
                self.cur_job.State = "teragrid:pending"
            elif self.text.find("h") >= 0: # held - hr
                self.cur_job.State = "teragrid:held"
            elif self.text == "t": # transfering
                self.cur_job.State = "teragrid:pending"
            else:
                self.step.warning("found unknown SGE job state '" + self.text + "'")
                self.cur_job.State = "teragrid:unknown"
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
        
##############################################################################################################

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

##############################################################################################################

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

##############################################################################################################
