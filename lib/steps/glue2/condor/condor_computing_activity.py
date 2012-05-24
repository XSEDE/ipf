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

logger = logging.getLogger("CondorJobsAgent")

##############################################################################################################

class CondorJobsAgent(ComputingActivitiesAgent):
    def __init__(self, args={}):
        ComputingActivitiesAgent.__init__(self,args)
        self.name = "teragrid.glue2.CondorJobsAgent"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document of type "+doc.type)

        condor_q = "condor_q"
        try:
            condor_q = self.config.get("condor","condor_q")
        except ConfigParser.Error:
            pass

        cmd = condor_q + " -long"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("condorq failed: "+output)
            raise AgentError("condorq failed: "+output+"\n")

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
        job = ComputingActivity()

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
                if status == "1":
                    job.State = "teragrid:pending"
                elif status == "2":
                    job.State = "teragrid:running"
                elif status == "3":
                    job.State = "teragrid:terminated"
                elif status == "4":
                    job.State = "teragrid:finished"
                elif status == "5":
                    job.State = "teragrid:held"
                else:
                    logger.warn("found unknown Condor job status '" + status + "'")
                    job.State = "teragrid:unknown"

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
                job.ComputingManagerSubmissionTime = self._getDateTime(line.split()[2])
            if line.startswith("JobStartDate = "):
                job.StartTime = self._getDateTime(line.split()[2])
            if line.startswith("CompletionDate = "):
                date = line.split()[2]
                if date != "0":
                    job.ComputingManagerEndTime = self._getDateTime(date)

        if clusterId == None or procId == None:
            logger.error("didn't find cluster or process ID in " + jobString)
            return None

        job.LocalIDFromManager = clusterId+"."+procId
        job.ID = "http://"+self._getSystemName()+"/glue2/ComputingActivity/"+job.LocalIDFromManager

        return job

    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # string containing the epoch time
        return datetime.datetime.fromtimestamp(float(aStr),localtzoffset())

##############################################################################################################

if __name__ == "__main__":    
    agent = CondorJobsAgent.createFromCommandLine()
    agent.runStdinStdout()
