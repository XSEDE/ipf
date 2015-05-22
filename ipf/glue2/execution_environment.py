
###############################################################################
#   Copyright 2011-2014 The University of Texas at Austin                     #
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
import json
import os
import re
import socket
import time
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.sysinfo import ResourceName
from ipf.sysinfo import Platform

from .resource import *
from .step import GlueStep

#######################################################################################################################

class ExecutionEnvironmentsStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "Produces a document containing one or more GLUE 2 ExecutionEnvironment. For a batch scheduled system, an ExecutionEnivonment is typically a compute node."
        self.time_out = 30
        self.requires = [ResourceName,Platform]
        self.produces = [ExecutionEnvironments]
        self._acceptParameter("queues",
                              "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. The expression is processed in order and the value for a queue at the end determines if it is shown.",
                              False)

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        
        host_groups = self._run()
        for host_group in host_groups:
            host_group.id = "%s.%s" % (host_group.Name,self.resource_name)
            host_group.ID = "urn:glue2:ExecutionEnvironment:%s.%s" % (host_group.Name,self.resource_name)
            host_group.ManagerID = "urn:glue2:ComputingManager:%s" % (self.resource_name)

        self._output(ExecutionEnvironments(self.resource_name,host_groups))

    def _shouldUseName(self, hosts):
        names = set()
        for host in hosts:
            names.add(host.Name)
        if len(names) == 1 or len(names) < len(hosts):
            return True
        else:
            return False

    def _groupHosts(self, hosts):
        use_name = self._shouldUseName(hosts)
        host_groups = []
        for host in hosts:
            for host_group in host_groups:
                if host.sameHostGroup(host_group,use_name):
                    if "UsedAverageLoad" in host.Extension:
                        host_load = host.Extension["UsedAverageLoad"]
                        if "UsedAverageLoad" not in host_group.Extension:
                            host_group.Extension["UsedAverageLoad"] = host_load
                        else:
                            host_group_load = host_group.Extension["UsedAverageLoad"]
                            host_group_load = (host_group_load * host_group.UsedInstances +
                                               host_load * host.UsedInstances) / \
                                               (host_group.UsedInstances + host.UsedInstances)
                            host_group.Extension["UsedAverageLoad"] = host_group_load
                    if "AvailableAverageLoad" in host.Extension:
                        host_load = host.Extension["AvailableAverageLoad"]
                        if "AvailableAverageLoad" not in host_group.Extension:
                            host_group.Extension["AvailableAverageLoad"] = host_load
                        else:
                            host_group_load = host_group.Extension["AvailableAverageLoad"]
                            host_group_avail = host_group.TotalInstances - host_group.UsedInstances - \
                                               host_group.UnavailableInstances
                            host_avail = host.TotalInstances - host.UsedInstances - host.UnavailableInstances
                            host_group_load = (host_group_load * host_group_avail + host_load * host_avail) / \
                                              (host_group_avail + host_group_avail)
                            host_group.Extension["AvailableAverageLoad"] = host_group_load
                    if "PartiallyUsedInstances" in host.Extension:
                        if "PartiallyUsedInstances" not in host_group.Extension:
                            host_group.Extension["PartiallyUsedInstances"] = host.Extension["PartiallyUsedInstances"]
                        else:
                            host_group.Extension["PartiallyUsedInstances"] = \
                              host_group.Extension["PartiallyUsedInstances"] + host.Extension["PartiallyUsedInstances"]
                    host_group.TotalInstances += host.TotalInstances
                    host_group.UsedInstances += host.UsedInstances
                    host_group.UnavailableInstances += host.UnavailableInstances
                    host = None
                    break
            if host is not None:
                host_groups.append(host)
                if not use_name:
                    host.Name = "NodeType%d" % len(host_groups)

        return host_groups

    def _run(self):
        raise StepError("ExecutionEnvironmentsStep._run not overriden")

    def _goodHost(self, host):
        # check that it has cpu information
        if host.PhysicalCPUs == None:
            return False

        # if the host is associated with a queue, check that it is a good one
        if len(host.ShareID) == 0:
            return True
        for share in host.ShareID:
            m = re.search("urn:glue2:ComputingShare:(\S+).%s" % self.resource_name,share)
            if self._includeQueue(m.group(1)):
                return True
        return False

#######################################################################################################################

class ExecutionEnvironment(Resource):
    def __init__(self):
        Resource.__init__(self)

        self.Platform = "unknown"           # string (Platform_t)
        self.VirtualMachine = None          # boolean (ExtendedBoolean)
        self.TotalInstances = None          # integer
        self.UsedInstances = None           # integer
        self.UnavailableInstances = None    # integer
        self.PhysicalCPUs = None            # integer
        self.LogicalCPUs = None             # integer
        self.CPUMultiplicity = None         # integer (CPUMultiplicity)
        self.CPUVendor = None               # string
        self.CPUModel = None                # string
        self.CPUVersion = None              # string
        self.CPUClockSpeed = None           # integer (MHz)
        self.CPUTimeScalingFactor = None    # float
        self.WallTimeScalingFactor = None   # float
        self.MainMemorySize = 0             # integer (MB)
        self.VirtualMemorySize = None       # integer (MB)
        self.OSFamily = "unknown"           # string (OSFamily)
        self.OSName = None                  # string (OSName)
        self.OSVersion = None               # string
        self.ConnectivityIn = None          # boolean (ExtendedBoolean)
        self.ConnectivityOut = None         # boolean (ExtendedBoolean)
        self.NetworkInfo = None             # string (NetworkInfo)
        # use Manager, Share, Activity from Resource, not ComputingManager, ComputingShare, ComputingActivity
        self.ApplicationEnvironmentID = []  # list of string (ID)
        self.BenchmarkID = []               # list of string (ID)

        # set defaults to be the same as the host where this runs
        (sysName,nodeName,release,version,machine) = os.uname()
        self.Platform = machine
        self.OSFamily = sysName.lower()
        self.OSName = sysName.lower()
        self.OSVersion = release

    def __str__(self):
        return json.dumps(ExecutionEnvironmentOgfJson(self).toJson(),sort_keys=True,indent=4)

    def sameHostGroup(self, exec_env, useName):
        if useName and self.Name != exec_env.Name:
            return False
        if self.Platform != exec_env.Platform:
            return False
        if self.PhysicalCPUs != exec_env.PhysicalCPUs:
            return False
        if self.LogicalCPUs != exec_env.LogicalCPUs:
            return False
        if self.CPUVendor != exec_env.CPUVendor:
            return False
        if self.CPUModel != exec_env.CPUModel:
            return False
        if self.CPUVersion != exec_env.CPUVersion:
            return False
        if self.CPUClockSpeed != exec_env.CPUClockSpeed:
            return False
        if self.MainMemorySize != exec_env.MainMemorySize:
            return False
        #if self.VirtualMemorySize != exec_env.VirtualMemorySize:
        #    return False
        if self.OSFamily != exec_env.OSFamily:
            return False
        if self.OSName != exec_env.OSName:
            return False
        if self.OSVersion != exec_env.OSVersion:
            return False

        if len(self.ShareID) != len(exec_env.ShareID):
            return False
        for share in self.ShareID:
            if not share in exec_env.ShareID:
                return False

        return True

#######################################################################################################################

class ExecutionEnvironmentTeraGridXml(ResourceTeraGridXml):
    data_cls = ExecutionEnvironment

    def __init__(self, data):
        ResourceTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ExecutionEnvironment")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        ResourceTeraGridXml.addToDomElement(self,doc,element)

        if self.data.Platform is not None:
            e = doc.createElement("Platform")
            e.appendChild(doc.createTextNode(self.data.Platform))
            element.appendChild(e)
        if self.data.VirtualMachine is not None:
            e = doc.createElement("VirtualMachine")
            if self.data.VirtualMachine:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.TotalInstances is not None:
            e = doc.createElement("TotalInstances")
            e.appendChild(doc.createTextNode(str(self.data.TotalInstances)))
            element.appendChild(e)
        if self.data.UsedInstances is not None:
            e = doc.createElement("UsedInstances")
            e.appendChild(doc.createTextNode(str(self.data.UsedInstances)))
            element.appendChild(e)
        if self.data.UnavailableInstances is not None:
            e = doc.createElement("UnavailableInstances")
            e.appendChild(doc.createTextNode(str(self.data.UnavailableInstances)))
            element.appendChild(e)
        if self.data.PhysicalCPUs is not None:
            e = doc.createElement("PhysicalCPUs")
            e.appendChild(doc.createTextNode(str(self.data.PhysicalCPUs)))
            element.appendChild(e)
        if self.data.LogicalCPUs is not None:
            e = doc.createElement("LogicalCPUs")
            e.appendChild(doc.createTextNode(str(self.data.LogicalCPUs)))
            element.appendChild(e)
        if self.data.CPUMultiplicity is not None:
            e = doc.createElement("CPUMultiplicity")
            e.appendChild(doc.createTextNode(self.data.CPUMultiplicity))
            element.appendChild(e)
        if self.data.CPUVendor is not None:
            e = doc.createElement("CPUVendor")
            e.appendChild(doc.createTextNode(self.data.CPUVendor))
            element.appendChild(e)
        if self.data.CPUModel is not None:
            e = doc.createElement("CPUModel")
            e.appendChild(doc.createTextNode(self.data.CPUModel))
            element.appendChild(e)
        if self.data.CPUVersion is not None:
            e = doc.createElement("CPUVersion")
            e.appendChild(doc.createTextNode(self.data.CPUVersion))
            element.appendChild(e)
        if self.data.CPUClockSpeed is not None:
            e = doc.createElement("CPUClockSpeed")
            e.appendChild(doc.createTextNode(str(self.data.CPUClockSpeed)))
            element.appendChild(e)
        if self.data.CPUTimeScalingFactor is not None:
            e = doc.createElement("CPUTimeScalingFactor")
            e.appendChild(doc.createTextNode(str(self.data.CPUTimeScalingFactor)))
            element.appendChild(e)
        if self.data.WallTimeScalingFactor is not None:
            e = doc.createElement("WallTimeScalingFactor")
            e.appendChild(doc.createTextNode(str(self.data.WallTimeScalingFactor)))
            element.appendChild(e)
        if self.data.MainMemorySize is not None:
            e = doc.createElement("MainMemorySize")
            e.appendChild(doc.createTextNode(str(self.data.MainMemorySize)))
            element.appendChild(e)
        if self.data.VirtualMemorySize is not None:
            e = doc.createElement("VirtualMemorySize")
            e.appendChild(doc.createTextNode(str(self.data.VirtualMemorySize)))
            element.appendChild(e)
        if self.data.OSFamily is not None:
            e = doc.createElement("OSFamily")
            e.appendChild(doc.createTextNode(self.data.OSFamily))
            element.appendChild(e)
        if self.data.OSName is not None:
            e = doc.createElement("OSName")
            e.appendChild(doc.createTextNode(self.data.OSName))
            element.appendChild(e)
        if self.data.OSVersion is not None:
            e = doc.createElement("OSVersion")
            e.appendChild(doc.createTextNode(self.data.OSVersion))
            element.appendChild(e)
        if self.data.ConnectivityIn == None:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("undefined"))
            element.appendChild(e)
        elif self.data.ConnectivityIn:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("true"))
            element.appendChild(e)
        else:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.ConnectivityOut == None:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("undefined"))
            element.appendChild(e)
        elif self.data.ConnectivityOut:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("true"))
            element.appendChild(e)
        else:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.NetworkInfo is not None:
            e = doc.createElement("NetworkInfo")
            e.appendChild(doc.createTextNode(self.data.NetworkInfo))
            element.appendChild(e)
        if self.data.ManagerID is not None:
            e = doc.createElement("ComputingManager")
            e.appendChild(doc.createTextNode(self.data.ManagerID))
            element.appendChild(e)
        for share in self.data.ShareID:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            element.appendChild(e)
        for activity in self.data.ActivityID:
            e = doc.createElement("ComputingActivity")
            e.appendChild(doc.createTextNode(activity))
            element.appendChild(e)
        for appEnv in self.data.ApplicationEnvironmentID:
            e = doc.createElement("ApplicationEnvironment")
            e.appendChild(doc.createTextNode(appEnv))
            element.appendChild(e)
        for benchmark in self.data.BenchmarkID:
            e = doc.createElement("Benchmark")
            e.appendChild(doc.createTextNode(benchmark))
            element.appendChild(e)

#######################################################################################################################

class ExecutionEnvironmentOgfJson(ResourceOgfJson):
    data_cls = ExecutionEnvironment

    def __init__(self, data):
        ResourceOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = ResourceOgfJson.toJson(self)

        doc["Platform"] = self.data.Platform
        if self.data.VirtualMachine is not None:
            doc["VirtualMachine"] = self.data.VirtualMachine
        if self.data.TotalInstances is not None:
            doc["TotalInstances"] = self.data.TotalInstances
        if self.data.UsedInstances is not None:
            doc["UsedInstances"] = self.data.UsedInstances
        if self.data.UnavailableInstances is not None:
            doc["UnavailableInstances"] = self.data.UnavailableInstances
        if self.data.PhysicalCPUs is not None:
            doc["PhysicalCPUs"] = self.data.PhysicalCPUs
        if self.data.LogicalCPUs is not None:
            doc["LogicalCPUs"] = self.data.LogicalCPUs
        if self.data.CPUMultiplicity is not None:
            doc["CPUMultiplicity"] = self.data.CPUMultiplicity
        if self.data.CPUVendor is not None:
            doc["CPUVendor"] = self.data.CPUVendor
        if self.data.CPUModel is not None:
            doc["CPUModel"] = self.data.CPUModel
        if self.data.CPUVersion is not None:
            doc["CPUVersion"] = self.data.CPUersion
        if self.data.CPUClockSpeed is not None:
            doc["CPUClockSpeed"] = self.data.CPUClockSpeed
        if self.data.CPUTimeScalingFactor is not None:
            doc["CPUTimeScalingFactor"] = self.data.CPUTimeScalingFactor
        if self.data.WallTimeScalingFactor is not None:
            doc["WallTimeScalingFactor"] = self.data.WallTimeScalingFactor
        doc["MainMemorySize"] = self.data.MainMemorySize
        if self.data.VirtualMemorySize is not None:
            doc["VirtualMemorySize"] = self.data.VirtualMemorySize
        doc["OSFamily"] = self.data.OSFamily
        if self.data.OSName is not None:
            doc["OSName"] = self.data.OSName
        if self.data.OSVersion is not None:
            doc["OSVersion"] = self.data.OSVersion
        doc["ConnectivityIn"] = self.data.ConnectivityIn
        doc["ConnectivityOut"] = self.data.ConnectivityOut
        if self.data.NetworkInfo is not None:
            doc["NetworkInfo"] = self.data.NetworkInfo
        if len(self.data.ApplicationEnvironmentID) > 0:
            doc["ApplicationEnvironmentID"] = self.data.ApplicationEnvironmentID
        if len(self.data.BenchmarkID) > 0:
            doc["BenchmarkID"] = self.BenchmarkID
            
        return doc

#######################################################################################################################

class ExecutionEnvironments(Data):
    def __init__(self, id, exec_envs=[]):
        Data.__init__(self,id)
        self.exec_envs = exec_envs
        
#######################################################################################################################

class ExecutionEnvironmentsTeraGridXml(Representation):
    data_cls = ExecutionEnvironments

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom().toprettyxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for exec_env in self.data.exec_envs:
            eedoc = ExecutionEnvironmentTeraGridXml.toDom(exec_env)
            doc.documentElement.appendChild(eedoc.documentElement.firstChild)
        return doc

#######################################################################################################################

class ExecutionEnvironmentsOgfJson(Representation):
    data_cls = ExecutionEnvironments

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        eedoc = []
        for exec_env in self.data.exec_envs:
            eedoc.append(ExecutionEnvironmentOgfJson(exec_env).toJson())
        return eedoc

#######################################################################################################################
