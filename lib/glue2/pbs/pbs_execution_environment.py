
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

from ipf.error import StepError
from glue2.execution_environment import *
from glue2.teragrid.platform import PlatformMixIn

#######################################################################################################################

class PbsExecutionEnvironmentsStep(ExecutionEnvironmentsStep):
    def __init__(self):
        ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("pbsnodes","the path to the PBS pbsnodes program (default 'pbsnodes')",False)
        self._acceptParameter("nodes",
                              "An expression describing the nodes to include (optional). The syntax is a series of +<property> and -<property> where <property> is the name of a node property or a '*'. '+' means include '-' means exclude. The expression is processed in order and the value for a node at the end determines if it is shown.",
                              False)

    def _run(self):
        pbsnodes = self.params.get("pbsnodes","pbsnodes")

        cmd = pbsnodes + " -a"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("pbsnodes failed: "+output)
            raise StepError("pbsnodes failed: "+output+"\n")

        nodeStrings = output.split("\n\n")
        hosts = map(self._getHost,nodeStrings)
        hosts = filter(self._testProperties,hosts)
        hosts = filter(self._goodHost,hosts)
        return hosts

    def _getHost(self, nodeString):
        host = ExecutionEnvironment()

        host.properties = ()

        lines = nodeString.split("\n")

        # ID set by ExecutionEnvironment
        host.Name = lines[0]
        various = False
        for line in lines[1:]:
            if line.find("state =") >= 0:
                if line.find("free") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 0
                elif line.find("offline") >= 0 or line.find("down") >= 0:
                    host.UsedInstances = 0
                    host.UnavailableInstances = 1
                elif line.find("job-exclusive") or line.find("job-busy") >= 0:
                    host.UsedInstances = 1
                    host.UnavailableInstances = 0
                elif line.find("<various>") >= 0:
                    various = True
                host.TotalInstances = 1
            if various and line.find("resources_assigned.ncpus =") >= 0:
                # when state is <various>, figure out used based on assigned cpus
                host.UnavailableInstances = 0
                host.UsedInstances = 0
                if host.PhysicalCPUs != None:
                    assignedCpus = int(line.split()[2])
                    if assignedCpus == host.PhysicalCPUs:
                        host.UsedInstances = 1
            if line.find("np =") >= 0 or line.find("resources_available.ncpus =") >= 0:
                cpus = int(line.split()[2])
                if (host.PhysicalCPUs == None) or (cpus > host.PhysicalCPUs):
                    host.PhysicalCPUs = cpus
                    host.LogicalCPUs = host.PhysicalCPUs        # don't have enough info to do anything else...
            if line.find("resources_available.mem =") >= 0:
                memSize = line.split("=")[1]
                host.MainMemorySize = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
            if line.find("resources_available.vmem =") >= 0:
                memSize = line.split("=")[1]
                host.VirtualMemorySize = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
            if line.find("status =") >= 0:
                toks = line[14:].split(",")
                for tok in toks:
                    if tok.find("totmem=") >= 0:
                        memSize = tok.split("=")[1]
                        totMem = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
                    if tok.find("physmem=") >= 0:
                        memSize = tok.split("=")[1]
                        host.MainMemorySize = int(memSize[:len(memSize)-2]) / 1024 # assuming KB
                    if tok.find("opsys=") >= 0:
                        if tok.split("=")[1] == "linux":
                            host.OSFamily = "linux"
                    if tok.find("uname=") >= 0:
                        utoks = tok.split()
                        host.Platform = utoks[len(utoks)-1]
			host.OSVersion = utoks[2]
                    if tok.find("ncpus=") >= 0:
                        cpus = int(tok.split("=")[1])
                        if (host.PhysicalCPUs == None) or (cpus > host.PhysicalCPUs):
                            host.PhysicalCPUs = cpus
                            host.LogicalCPUs = host.PhysicalCPUs        # don't have enough info to do anything else...
                    if tok.find("loadave=") >= 0:
                        load = float(tok.split("=")[1])
                        if host.UsedInstances > 0:
                            host.Extension["UsedAverageLoad"] = load
                        elif host.UnavailableInstances == 0:
                            host.Extension["UsedAvailableLoad"] = load
                host.VirtualMemorySize = totMem - host.MainMemorySize
            if line.find("properties =") >= 0:
                host.properties = line[18:].split(",")
        return host
        
    def _testProperties(self, host):
        nodes = self.params.get("nodes","+*")
        toks = nodes.split()
        goodSoFar = False
        for tok in toks:
            if tok[0] == '+':
                prop = tok[1:]
                if (prop == "*") or (prop in host.properties):
                    goodSoFar = True
            elif tok[0] == '-':
                prop = tok[1:]
                if (prop == "*") or (prop in host.properties):
                    goodSoFar = False
            else:
                self.warn("can't parse part of nodes expression: "+tok)
        return goodSoFar

#######################################################################################################################

class TeraGridPbsExecutionEnvironmentsStep(PbsExecutionEnvironmentsStep, PlatformMixIn):
    def __init__(self):
        PbsExecutionEnvironmentsStep.__init__(self)
        PlatformMixIn.__init__(self)

    def _run(self):
        hosts = PbsExecutionEnvironmentsStep._run(self)
        self.addTeraGridPlatform(hosts)
        return hosts

#######################################################################################################################
