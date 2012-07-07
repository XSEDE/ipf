
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
import os
import re
import xml.sax
import xml.sax.handler

from ipf.error import StepError
from glue2.execution_environment import *
from glue2.teragrid.platform import PlatformMixIn

#######################################################################################################################

class NimbusExecutionEnvironmentsStep(ExecutionEnvironmentsStep):

    def __init__(self, params):
        ExecutionEnvironmentsStep.__init__(self,params)

        self.name = "glue2/nimbus/execution_environments"
        self.accepts_params["nimbus_dir"] = "the path to the Nimbus directory (optional - for specifying location of nimbus-nodes command)"
        self.accepts_params["cores_per_node"] = "the number of processing cores per node"

    def _run(self):
        try:
            nimbus_nodes = os.path.join(self.params["nimbus_dir"],"bin","nimbus-nodes")
        except KeyError:
            nimbus_nodes = "nimbus-nodes"

        cmd = nimbus_nodes + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("nimbus-nodes failed: "+output+"\n")

        nodeStrings = output.split("\n\n")
        return map(self._getNode,nodeStrings)

    def _getNode(self, nodeString):
        lines = nodeString.split("\n")

        node = ExecutionEnvironment()
        node.TotalInstances = 1
        try:
            node.LogicalCPUs = self.params["cores_per_node"]
        except KeyError:
            pass
        available_memory = None
        for line in lines:
            if "hostname" in line:
                pass
            elif "pool" in line:
                node.Name = line.split()[2]
            elif "memory available" in line:
                available_memory = int(line.split()[3])
            elif "memory" in line:
                node.MainMemorySize = int(line.split()[2])
            elif "in_use" in line:
                if line.split()[2] == "true":
                    # only know memory allocated, so just use it
                    if available_memory == 0:
                        node.UsedInstances = 1
                    else:
                        node.UsedInstances = 0
                else:
                    node.UsedInstances = 0
            elif "active" in line:
                if line.split()[2] == "true":
                    node.UnavailableInstances = 1
                else:
                    node.UnavailableInstances = 0
        return node

#######################################################################################################################
