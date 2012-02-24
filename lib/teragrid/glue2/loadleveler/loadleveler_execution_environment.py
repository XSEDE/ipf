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

logger = logging.getLogger("LoadLevelerExecutionEnvironment")

##############################################################################################################

class LoadLevelerExecutionEnvironmentsAgent(ExecutionEnvironmentsAgent):
    def __init__(self, args={}):
        ExecutionEnvironmentsAgent.__init__(self)
        self.name = "teragrid.glue2.LoadLevelerExecutionEnvironment"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document "+doc.id)

        llstatus = "llstatus"
        try:
            llstatus = self.config.get("loadleveler","llstatus")
        except ConfigParser.Error:
            pass

        cmd = llstatus + " -l"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("llstatus failed: "+output)
            raise AgentError("llstatus failed: "+output+"\n")

        nodeStrings = []

        curIndex = 0
        nextIndex = output.find("===============================================================================",1)
        while nextIndex != -1:
            nodeStrings.append(output[curIndex:nextIndex])
            curIndex = nextIndex
            nextIndex = output.find("===============================================================================",
                                    curIndex+1)
        nodeStrings.append(output[curIndex:])

        hosts = []
        for nodeString in nodeStrings:
            host = self._getHost(nodeString)
            if self._goodHost(host):
                hosts.append(host)

        return self._groupHosts(hosts)

    def _getHost(self, nodeString):
        host = ExecutionEnvironment()
        host.ComputingManager = "http://"+self._getSystemName()+"/glue2/ComputingManager/SGE"

        lines = nodeString.split("\n")

        load = None
        # ID set by ExecutionEnvironment
        for line in lines[1:]:
            if line.startswith("Name "):
                host.Name = line[line.find("=")+2:]
            if line.startswith("LoadAvg "):
                load = float(line[line.find("=")+2:])
            if line.startswith("State "):
                host.TotalInstances = 1
                if line.find("Busy") >= 0:
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif line.find("Running") >= 0: # ?
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif line.find("Idle") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                elif line.find("Down") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 1
                elif line.find("None") >= 0: # central manager seems to have a state of None
                    host.TotalInstances = 0 # don't include this host
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                else: # guess starting and stopping
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                host.TotalInstances = 1
                if load != None:
                    if host.UsedInstances > 0:
                        host.Extension["UsedAverageLoad"] = load
                    elif host.UnavailableInstances == 0:
                        host.Extension["AvailableAverageLoad"] = load
            # Not sure of the best way to get LogicalCPUs. I'm using it to calculate slots, so probably 2nd way
            if line.startswith("Cpus "):
                host.PhysicalCPUs = int(line[line.find("=")+2:])
                #host.LogicalCPUs = host.PhysicalCPUs
            if line.startswith("Max_Starters "):
                host.LogicalCPUs = int(line[line.find("=")+2:])
            if line.startswith("OpSys "):
                if line.find("Linux"):
                    host.OSFamily = "linux"
            if line.startswith("Arch "):
                host.Platform = line[line.find("=")+2:]
            if line.startswith("Memory "):
                host.MainMemorySize = self._getMB(line[line.find("=")+2:].split())
            if line.startswith("VirtualMemory "):
                host.VirtualMemorySize = self._getMB(line[line.find("=")+2:].split())
        return host

    def _getMB(self, namevalue):
        (value,units) = namevalue
        if units == "kb":
            return int(value) / 1024
        if units == "mb":
            return int(value)
        if units == "gb":
            return int(value) * 1024
        
##############################################################################################################

if __name__ == "__main__":    
    agent = LoadLevelerExecutionEnvironmentsAgent.createFromCommandLine()
    agent.runStdinStdout()
