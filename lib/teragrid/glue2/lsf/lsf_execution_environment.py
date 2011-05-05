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
from teragrid.glue2.computing_activity import includeQueue
from teragrid.glue2.execution_environment import *

logger = logging.getLogger("LsfExecutionEnvironment")

##############################################################################################################

# the Queues argument is defined in ComputingActivity

##############################################################################################################

class LsfExecutionEnvironmentsAgent(ExecutionEnvironmentsAgent):
    def __init__(self, args={}):
        ExecutionEnvironmentsAgent.__init__(self)
        self.name = "teragrid.glue2.LsfExecutionEnvironment"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document "+doc.id)

        lshosts = "lshosts"
        try:
            lshosts = self.config.get("lsf","lshosts")
        except ConfigParser.Error:
            pass

        cmd = lshosts + " -w"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("lshosts failed: "+output)
            raise AgentError("lshosts failed: "+output+"\n")

        lshostsRecords = {}
        lines = output.split("\n")
        for index in range(1,len(lines)):
            rec = LsHostsRecord(lines[index])
            lshostsRecords[rec.hostName] = rec

        bhosts = "bhosts"
        try:
            bhosts = self.config.get("lsf","bhosts")
        except ConfigParser.Error:
            pass

        cmd = bhosts + " -w"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("bhosts failed: "+output)
            raise AgentError("bhosts failed: "+output+"\n")

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
                logger.warn("no bhost record found for "+host)
                break
            all_hosts.append(self._getHost(lshost,bhost))

        hosts = []
        for host in all_hosts:
            if self._goodHost(host):
                hosts.append(host)

        host_groups = []
        for host in hosts:
            for host_group in host_groups:
                if host.sameHostGroup(host_group):
                    host_group.TotalInstances = host_group.TotalInstances + host.TotalInstances
                    host_group.UsedInstances = host_group.UsedInstances + host.UsedInstances
                    host_group.UnavailableInstances = host_group.UnavailableInstances + host.UnavailableInstances
                    host = None
                    break
            if host != None:
                host_groups.append(host)

        for index in range(0,len(host_groups)):
            host_groups[index].Name = "NodeType" + str(index+1)
            host_groups[index].ID = "http://"+self._getSystemName()+"/glue2/ExecutionEnvironment/"+ \
                                    host_groups[index].Name

        for host_group in host_groups:
            host_group.id = host_group.Name+"."+self._getSystemName()

        return host_groups

    def _getHost(self, lshost, bhost):
        host = ExecutionEnvironment()
        host.ComputingManager = "http://"+self._getSystemName()+"/glue2/ComputingManager/SGE"

        # ID set by ExecutionEnvironment
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
            logger.warn("unknown status: " + bhostsRecord.status)

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

##############################################################################################################

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

##############################################################################################################

if __name__ == "__main__":    
    agent = LsfExecutionEnvironmentsAgent.createFromCommandLine()
    agent.runStdinStdout()
