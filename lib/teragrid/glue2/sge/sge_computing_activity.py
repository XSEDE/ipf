#!/usr/bin/env python

###############################################################################
#   Copyright 2011 The University of Texas at Austin                          #
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
import logging
import os
import re
import sys
import xml.sax
import xml.sax.handler
import ConfigParser

from ipf.error import *
from teragrid.glue2.computing_activity import *

logger = logging.getLogger("SgeJobsAgent")

##############################################################################################################

class SgeJobsAgent(ComputingActivitiesAgent):
    def __init__(self, args={}):
        ComputingActivitiesAgent.__init__(self,args)
        self.name = "teragrid.glue2.SgeJobsAgent"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        qstat = "qstat"
        try:
            qstat = self.config.get("sge","qstat")
        except ConfigParser.Error:
            pass

        cmd = qstat + " -xml -pri -u \\*"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("qstat failed: "+output)
            raise AgentError("qstat failed: "+output+"\n")

        #udom = xml.dom.minidom.parseString(output)

        uhandler = JobsUHandler(self._getSystemName(),self.hide)
        xml.sax.parseString(output,uhandler)

        jobs = {}
        for job in uhandler.jobs:
            jobs[job.LocalIDFromManager] = job

        cmd = qstat + " -xml -j \\*"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("qstat failed: "+output)
            raise AgentError("qstat failed: "+output+"\n")

        # dom parsing takes way too long
        #udom = xml.dom.minidom.parseString(output)

        jhandler = JobsJHandler(jobs)
        try:
            xml.sax.parseString(output,jhandler)
        except xml.sax.SAXParseException, e:
            # sax parsing fails sometimes
            logger.warn("parsing of XML output from qstat -j failed, parsing line by line instead")
            self.parseJLines(output,jobs)

        jobList = []
        for job in uhandler.jobs:
            if includeQueue(self.config,job.Queue):
                jobList.append(job)

        for job in jobList:
            job.id = job.LocalIDFromManager+"."+self._getSystemName()

        return jobList

    def parseJLines(self, output, jobs):
        H_RT = 1
        MEM_TOTAL = 2
        cur_resource = None
        
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
                cur_job.ComputingShare = ["http://"+self._getSystemName()+"/glue2/ComputingShare/"+cur_job.Queue]
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
                cur_job.SubmissionTime = datetime.datetime.fromtimestamp(int(m.group(1)),localtzoffset())
                cur_job.ComputingManagerSubmissionTime = cur_job.SubmissionTime
                continue

##############################################################################################################

        # this indicates that SGE should reserve resources for this job (and sorta backfill around it)
        #if line.startswith("reserve:"):
        #if line.split()[1] == "y":
        #self.Extension["SgeReserve"] = "yes"

##############################################################################################################

class JobsUHandler(xml.sax.handler.ContentHandler):

    # get submission time from qstat -j

    def __init__(self, system_name, hide):
        self.system_name = system_name
        self.hide = hide
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
            self.cur_job = ComputingActivity()
            self.cur_job.hide = self.hide
            self.cur_job.LocalIDFromManager = self.text
            self.cur_job.ID = "http://"+self.system_name+"/glue2/ComputingActivity/"+self.text
        if name == "JAT_prio":
            self.priority = float(self.text)
        if name == "JB_name":
            self.cur_job.Name = self.text
        if name == "JB_owner":
            self.cur_job.LocalOwner = self.text
        if name == "state":
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
                logger.warn("found unknown SGE job state '" + self.text + "'")
                self.cur_job.State = "teragrid:unknown"
        if name == "slots":
            self.cur_job.RequestedSlots = int(self.text)
            if self.cur_job.StartTime != None:
                usedWallTime = int(self.cur_time - time.mktime(self.cur_job.StartTime.timetuple()))
                self.cur_job.UsedTotalWallTime = usedWallTime * self.cur_job.RequestedSlots

        if name == "JAT_start_time":
            self.cur_job.StartTime = _getDateTime(self.text)

    def characters(self, ch):
        # all of the text for an element may not come at once
        self.text = self.text + ch
        
##############################################################################################################

class JobsJHandler(xml.sax.handler.ContentHandler):

    RESOURCE_MEM_TOTAL = 1
    RESOURCE_H_RT = 2

    def __init__(self, jobs):
        self.cur_resource = None
        self.cur_job = None
        self.jobs = jobs
        self.text = ""
        
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
            self.cur_job.SubmissionTime = datetime.datetime.fromtimestamp(int(self.text),localtzoffset())
            self.cur_job.ComputingManagerSubmissionTime = self.cur_job.SubmissionTime

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

if __name__ == "__main__":    
    agent = SgeJobsAgent.createFromCommandLine()
    agent.runStdinStdout()
