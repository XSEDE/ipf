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

logger = logging.getLogger("CondorExecutionEnvironment")

##############################################################################################################

class CondorExecutionEnvironmentsAgent(ExecutionEnvironmentsAgent):
    def __init__(self, args={}):
        ExecutionEnvironmentsAgent.__init__(self)
        self.name = "teragrid.glue2.CondorExecutionEnvironment"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document "+doc.id)

        condor_status = "condor_status"
        try:
            condor_status = self.config.get("condor","condor_status")
        except ConfigParser.Error:
            pass

        cmd = condor_status + " -long"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("condor_status failed: "+output)
            raise AgentError("condor_status failed: "+output+"\n")

        node_strings = output.split("\n\n")

        hosts = []
        for node_string in node_strings:
            host = self._getHost(node_string)
            if self._goodHost(host):
                hosts.append(host)

        return self._groupHosts(hosts)

    def _getHost(self, node_str):
        host = ExecutionEnvironment()
        host.ComputingManager = "http://"+self._getSystemName()+"/glue2/ComputingManager"

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
        
##############################################################################################################

if __name__ == "__main__":    
    agent = CondorExecutionEnvironmentsAgent.createFromCommandLine()
    agent.runStdinStdout()
