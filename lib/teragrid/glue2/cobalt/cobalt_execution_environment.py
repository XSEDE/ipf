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

logger = logging.getLogger("CobaltExecutionEnvironment")

##############################################################################################################

class CobaltExecutionEnvironmentsAgent(ExecutionEnvironmentsAgent):
    def __init__(self, args={}):
        ExecutionEnvironmentsAgent.__init__(self)
        self.name = "teragrid.glue2.CobaltExecutionEnvironment"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document "+doc.id)

        partlist = "partlist"
        try:
            partlist = self.config.get("cobalt","partlist")
        except ConfigParser.Error:
            pass

        cmd = partlist + " -a"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("partlist failed: "+output)
            raise AgentError("partlist failed: "+output+"\n")


        lines = output.split("\n")

        availNodes = 0
        unavailNodes = 0
        usedNodes = 0
        blocking = []
        smallestPartSize = -1
        largestPartSize = -1;
        for index in range(len(lines)-1,2,-1):
            #Name          Queue                             State                   Backfill
            #          1         2         3         4         5         6         7         8
            #012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
            toks = lines[index].split()
            toks2 = toks[0].split("_")

            partSize = int(toks2[0])

            if smallestPartSize == -1:
                smallestPartSize = partSize
            if partSize > largestPartSize:
                largestPartSize = partSize

            if partSize == smallestPartSize:
                toks2 = lines[index][48:].split()
                state = toks2[0]
                if state == "idle":
                    availNodes = availNodes + partSize
                elif state == "busy":
                    usedNodes = usedNodes + partSize
                elif state == "starting":
                    usedNodes = usedNodes + partSize
                elif state == "blocked":
                    if (lines[index].find("failed diags") != -1) or (lines[index].find("pending diags") != -1):
                        #blocked by pending diags
                        #failed diags
                        #blocked by failed diags
                        unavailNodes = unavailNodes + partSize
                    else:
                        blockedBy = toks2[1][1:len(toks2[1])-1]
                        if not blockedBy in blocking:
                            blocking.append(blockedBy)
                elif state == "hardware":
                    #hardware offline: nodecard <nodecard_id>
                    #hardware offline: switch <switch_id>
                    unavailNodes = unavailNodes + partSize
                else:
                    logger.warn("found unknown partition state: "+toks[2])

        # assuming that all nodes are identical

        execEnv = ExecutionEnvironment()
        try:
            execEnv.PhysicalCPUs = self.config.getint("cobalt","processors_per_node")
        except ConfigParser.Error:
            logger.error("cobalt.processors_per_node not specified")
            raise AgentError("cobalt.processors_per_node not specified")

        execEnv.LogicalCPUs = execEnv.PhysicalCPUs

        try:
            execEnv.MainMemorySize = self.config.getint("cobalt","node_memory_size")
        except ConfigParser.Error:
            logger.error("cobalt.node_memory_size not specified")
            raise AgentError("cobalt.node_memory_size not specified")
        #execEnv.VirtualMemorySize = 

        # use the defaults set for Platform, OSVersion, etc in ExecutionEnvironment (same as the login node)

        execEnv.UsedInstances = (totalNodes - availNodes - unavailNodes) * execEnv.PhysicalCPUs
        execEnv.TotalInstances = totalNodes * execEnv.PhysicalCPUs
        execEnv.UnavailableInstances = unavailNodes * execEnv.PhysicalCPUs

        execEnv.Name = "NodeType1"
        execEnv.ID = "http://"+self.getSystemName()+"/glue2/ExecutionEnvironment/"+ execEnv.Name
        execEnv.id = execEnv.Name+"."+self._getSystemName()

        return [execEnv]
        
##############################################################################################################

if __name__ == "__main__":    
    agent = CobaltExecutionEnvironmentsAgent.createFromCommandLine()
    agent.runStdinStdout()
