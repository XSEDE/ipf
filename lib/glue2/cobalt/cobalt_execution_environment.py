
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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
from glue2.execution_environment import *
from glue2.teragrid.platform import PlatformMixIn

#######################################################################################################################

class CobaltExecutionEnvironmentsStep(ExecutionEnvironmentsStep):

    def __init__(self):
        ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("partlist","the path to the Cobalt partlist program (default 'partlist')",False)
        self._acceptParameter("cores_per_node",
                              "the number of processing cores per node is not provided by the Cobalt partlist program (default 8)",
                              False)
        self._acceptParameter("memory_per_node",
                              "the amount of memory per node (in MB) is not provided by the Cobalt partlist program (default 16384)",
                              False)

    def _run(self):
        partlist = self.params.get("partlist","partlist")

        cmd = partlist + " -a"
        selfr.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("partlist failed: "+output+"\n")

        lines = output.split("\n")

        avail_nodes = 0
        unavail_nodes = 0
        used_nodes = 0
        blocking = []
        smallest_partsize = -1
        largest_partsize = -1;
        for index in range(len(lines)-1,2,-1):
            #Name          Queue                             State                   Backfill
            #          1         2         3         4         5         6         7         8
            #012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
            toks = lines[index].split()
            toks2 = toks[0].split("_")

            partsize = int(toks2[0])

            if smallest_partsize == -1:
                smallest_partsize = partsize
            if partsize > largest_partsize:
                largest_partsize = partsize

            if partsize == smallest_partsize:
                toks2 = lines[index][48:].split()
                state = toks2[0]
                if state == "idle":
                    avail_nodes = avail_nodes + partsize
                elif state == "busy":
                    used_nodes = used_nodes + partsize
                elif state == "starting":
                    used_nodes = used_nodes + partsize
                elif state == "blocked":
                    if (lines[index].find("failed diags") != -1) or (lines[index].find("pending diags") != -1):
                        #blocked by pending diags
                        #failed diags
                        #blocked by failed diags
                        unavail_nodes = unavail_nodes + partsize
                    else:
                        blocked_by = toks2[1][1:len(toks2[1])-1]
                        if not blocked_by in blocking:
                            blocking.append(blocked_by)
                elif state == "hardware":
                    #hardware offline: nodecard <nodecard_id>
                    #hardware offline: switch <switch_id>
                    unavail_nodes = unavail_nodes + partsize
                else:
                    self.warning("found unknown partition state: "+toks[2])

        # assuming that all nodes are identical

        exec_env = ExecutionEnvironment()
        exec_env.LogicalCPUs = self.params.get("cores_per_node",8)
        exec_env.PhysicalCPUs = exec_env.LogicalCPUs

        exec_env.MainMemorySize = self.params.get("memory_per_node",16384)
        #exec_env.VirtualMemorySize = 

        # use the defaults set for Platform, OSVersion, etc in ExecutionEnvironment (same as the login node)

        exec_env.UsedInstances = used_nodes * exec_env.PhysicalCPUs
        exec_env.TotalInstances = (used_nodes + avail_nodes + unavail_nodes) * exec_env.PhysicalCPUs
        exec_env.UnavailableInstances = unavail_nodes * exec_env.PhysicalCPUs

        exec_env.Name = "NodeType1"

        return [exec_env]
        
#######################################################################################################################
