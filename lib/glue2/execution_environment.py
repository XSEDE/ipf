
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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
import socket
import time
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.resource_name import ResourceName

from glue2.step import GlueStep

#######################################################################################################################

class ExecutionEnvironmentsStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "Produces a document containing one or more GLUE 2 ExecutionEnvironment. For a batch scheduled system, an ExecutionEnivonment is typically a compute node."
        self.time_out = 30
        self.requires = [ResourceName]
        self.produces = [ExecutionEnvironments]
        self._acceptParameter("queues",
                              "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. The expression is processed in order and the value for a queue at the end determines if it is shown.",
                              False)

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        
        hosts = self._run()
        host_groups = self._groupHosts(hosts)

        for host_group in host_groups:
            host_group.id = "%s.%s" % (host_group.Name,self.resource_name)
            host_group.ID = "urn:glue2:ExecutionEnvironment:%s.%s" % (host_group.Name,self.resource_name)
            host_group.ComputingManager = "urn:glue2:ComputingManager:%s" % (self.resource_name)

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
        if len(host.ComputingShare) == 0:
            return True
        for queue in host.ComputingShare:
            if self._includeQueue(queue):
                return True
        return False

#######################################################################################################################

class ExecutionEnvironment(Data):
    def __init__(self):
        Data.__init__(self)
        
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = None
        self.ID = None
        self.Name = None
        self.OtherInfo = [] # strings
        self.Extension = {} # (key,value) strings

        # Resource
        self.Manager = None # string (uri)
        self.Share = []     # list of string (uri)
        self.Activity = []  # list of string (uri)

        # ExecutionEnvironment
        self.Platform = None                # string (Platform_t)
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
        self.OSFamily = None                # string (OSFamily)
        self.OSName = None                  # string (OSName)
        self.OSVersion = None               # string
        self.ConnectivityIn = "undefined"   # boolean (ExtendedBoolean)
        self.ConnectivityOut = "undefined"  # boolean (ExtendedBoolean)
        self.NetworkInfo = None             # string (NetworkInfo)
        self.ComputingManager = None        # string (uri)
        self.ComputingShare = []            # list of string (LocalID)
        self.ComputingActivity = []         # list of string (uri)
        self.ApplicationEnvironment = []    # list of string (LocalID)
        self.Benchmark = []                 # list of string (LocalID)

        # set defaults to be the same as the host where this runs
        (sysName,nodeName,release,version,machine) = os.uname()
        self.Platform = machine
        self.OSFamily = sysName.lower()
        self.OSName = sysName.lower()
        self.OSVersion = release

    def __str__(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

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

        if len(self.ComputingShare) != len(exec_env.ComputingShare):
            return False
        for share in self.ComputingShare:
            if not share in exec_env.ComputingShare:
                return False

        return True
    
    ###################################################################################################################

    def fromJson(self, doc):
        # Entity
        if "CreationTime" in doc:
            self.CreationTime = textToDateTime(doc["CreationTime"])
        else:
            self.CreationTime = None
        self.Validity = doc.get("Validity")
        self.ID = doc.get("ID")
        self.Name = doc.get("Name")
        self.OtherInfo = doc.get("OtherInfo",[])
        self.Extension = doc.get("Extension",{})

        # Resource
        self.Manager = doc.get("Manager")
        self.Share = doc.get("Share",[])
        self.Activity = doc.get("Activity",[])

        # ExecutionEnvironment
        self.Platform = doc.get("Platform")
        self.VirtualMachine = doc.get("VirtualMachine")
        self.TotalInstances = doc.get("TotalInstances")
        self.UsedInstances = doc.get("UsedInstances")
        self.UnavailableInstances = doc.get("UnavailableInstances")
        self.PhysicalCPUs = doc.get("PhysicalCPUs")
        self.LogicalCPUs = doc.get("LogicalCPUs")
        self.CPUMultiplicity = doc.get("CPUMultiplicity")
        self.CPUVencor = doc.get("CPUVendor")
        self.CPUModel = doc.get("CPUModel")
        self.CPUVersion = doc.get("CPUVersion")
        self.CPUClockSpeed = doc.get("CPUClockSpeed")
        self.CPUTimeScalingFactor = doc.get("CPUTimeScalingFactor")
        self.WallTimeScalingFactor = doc.get("WallTimeScalingFactor")
        self.MainMemorySize = doc.get("MainMemorySize")
        self.VirtualMemorySize = doc.get("VirtualMemorySize")
        self.OSFamily = doc.get("OSFamily")
        self.OSName = doc.get("OSName")
        self.OSVersion = doc.get("OSVersion")
        self.ConnectivityIn = doc.get("ConnectivityIn")
        self.ConnectivityOut = doc.get("ConnectivityOut")
        self.NetworkInfo = doc.get("NetworkInfo")
        self.ComputingManager = doc.get("ComputingManager")
        self.ComputingShare = doc.get("ComputingShare",[])
        self.ComputingActivity = doc.get("ComputingActivity",[])
        self.ApplicationEnvironment = doc.get("ApplicationEnvironment",[])
        self.Benchmark = doc.get("Benchmark",[])

#######################################################################################################################

class ExecutionEnvironmentTeraGridXml(Representation):
    data_cls = ExecutionEnvironment

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(exec_env):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ExecutionEnvironment")
        doc.documentElement.appendChild(root)

        # Entity
        e = doc.createElement("CreationTime")
        e.appendChild(doc.createTextNode(dateTimeToText(exec_env.CreationTime)))
        if exec_env.Validity is not None:
            e.setAttribute("Validity",str(exec_env.Validity))
        root.appendChild(e)

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(exec_env.ID))
        root.appendChild(e)

        if exec_env.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(exec_env.Name))
            root.appendChild(e)
        for info in exec_env.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        for key in exec_env.Extension.keys():
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(str(exec_env.Extension[key])))
            root.appendChild(e)

        # Resource
        if exec_env.Manager is not None:
            e = doc.createElement("Manager")
            e.appendChild(doc.createTextNode(exec_env.Manager))
            root.appendChild(e)
        for share in exec_env.Share:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for activity in exec_env.Activity:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(exec_env.Activity))
            root.appendChild(e)

        # ExecutionEnvironment
        if exec_env.Platform is not None:
            e = doc.createElement("Platform")
            e.appendChild(doc.createTextNode(exec_env.Platform))
            root.appendChild(e)
        if exec_env.VirtualMachine is not None:
            e = doc.createElement("VirtualMachine")
            if exec_env.VirtualMachine:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if exec_env.TotalInstances is not None:
            e = doc.createElement("TotalInstances")
            e.appendChild(doc.createTextNode(str(exec_env.TotalInstances)))
            root.appendChild(e)
        if exec_env.UsedInstances is not None:
            e = doc.createElement("UsedInstances")
            e.appendChild(doc.createTextNode(str(exec_env.UsedInstances)))
            root.appendChild(e)
        if exec_env.UnavailableInstances is not None:
            e = doc.createElement("UnavailableInstances")
            e.appendChild(doc.createTextNode(str(exec_env.UnavailableInstances)))
            root.appendChild(e)
        if exec_env.PhysicalCPUs is not None:
            e = doc.createElement("PhysicalCPUs")
            e.appendChild(doc.createTextNode(str(exec_env.PhysicalCPUs)))
            root.appendChild(e)
        if exec_env.LogicalCPUs is not None:
            e = doc.createElement("LogicalCPUs")
            e.appendChild(doc.createTextNode(str(exec_env.LogicalCPUs)))
            root.appendChild(e)
        if exec_env.CPUMultiplicity is not None:
            e = doc.createElement("CPUMultiplicity")
            e.appendChild(doc.createTextNode(exec_env.CPUMultiplicity))
            root.appendChild(e)
        if exec_env.CPUVendor is not None:
            e = doc.createElement("CPUVendor")
            e.appendChild(doc.createTextNode(exec_env.CPUVendor))
            root.appendChild(e)
        if exec_env.CPUModel is not None:
            e = doc.createElement("CPUModel")
            e.appendChild(doc.createTextNode(exec_env.CPUModel))
            root.appendChild(e)
        if exec_env.CPUVersion is not None:
            e = doc.createElement("CPUVersion")
            e.appendChild(doc.createTextNode(exec_env.CPUVersion))
            root.appendChild(e)
        if exec_env.CPUClockSpeed is not None:
            e = doc.createElement("CPUClockSpeed")
            e.appendChild(doc.createTextNode(str(exec_env.CPUClockSpeed)))
            root.appendChild(e)
        if exec_env.CPUTimeScalingFactor is not None:
            e = doc.createElement("CPUTimeScalingFactor")
            e.appendChild(doc.createTextNode(str(exec_env.CPUTimeScalingFactor)))
            root.appendChild(e)
        if exec_env.WallTimeScalingFactor is not None:
            e = doc.createElement("WallTimeScalingFactor")
            e.appendChild(doc.createTextNode(str(exec_env.WallTimeScalingFactor)))
            root.appendChild(e)
        if exec_env.MainMemorySize is not None:
            e = doc.createElement("MainMemorySize")
            e.appendChild(doc.createTextNode(str(exec_env.MainMemorySize)))
            root.appendChild(e)
        if exec_env.VirtualMemorySize is not None:
            e = doc.createElement("VirtualMemorySize")
            e.appendChild(doc.createTextNode(str(exec_env.VirtualMemorySize)))
            root.appendChild(e)
        if exec_env.OSFamily is not None:
            e = doc.createElement("OSFamily")
            e.appendChild(doc.createTextNode(exec_env.OSFamily))
            root.appendChild(e)
        if exec_env.OSName is not None:
            e = doc.createElement("OSName")
            e.appendChild(doc.createTextNode(exec_env.OSName))
            root.appendChild(e)
        if exec_env.OSVersion is not None:
            e = doc.createElement("OSVersion")
            e.appendChild(doc.createTextNode(exec_env.OSVersion))
            root.appendChild(e)
        if exec_env.ConnectivityIn == None:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("undefined"))
            root.appendChild(e)
        elif exec_env.ConnectivityIn:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("true"))
            root.appendChild(e)
        else:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if exec_env.ConnectivityOut == None:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("undefined"))
            root.appendChild(e)
        elif exec_env.ConnectivityOut:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("true"))
            root.appendChild(e)
        else:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if exec_env.NetworkInfo is not None:
            e = doc.createElement("NetworkInfo")
            e.appendChild(doc.createTextNode(exec_env.NetworkInfo))
            root.appendChild(e)
        if exec_env.ComputingManager is not None:
            e = doc.createElement("ComputingManager")
            e.appendChild(doc.createTextNode(exec_env.ComputingManager))
            root.appendChild(e)
        for share in exec_env.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for activity in exec_env.ComputingActivity:
            e = doc.createElement("ComputingActivity")
            e.appendChild(doc.createTextNode(activity))
            root.appendChild(e)
        for appEnv in exec_env.ApplicationEnvironment:
            e = doc.createElement("ApplicationEnvironment")
            e.appendChild(doc.createTextNode(appEnv))
            root.appendChild(e)
        for benchmark in exec_env.Benchmark:
            e = doc.createElement("Benchmark")
            e.appendChild(doc.createTextNode(benchmark))
            root.appendChild(e)
            
        return doc

#######################################################################################################################

class ExecutionEnvironmentIpfJson(Representation):
    data_cls = ExecutionEnvironment

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(exec_env):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(exec_env.CreationTime)
        if exec_env.Validity is not None:
            doc["Validity"] = exec_env.Validity
        doc["ID"] = exec_env.ID
        if exec_env.Name is not None:
            doc["Name"] = exec_env.Name
        if len(exec_env.OtherInfo) > 0:
            doc["OtherInfo"] = exec_env.OtherInfo
        if len(exec_env.Extension) > 0:
            doc["Extension"] = exec_env.Extension

        # Resource
        if exec_env.Manager is not None:
            doc["Manager"] = exec_env.Manager
        if len(exec_env.Share) > 0:
            doc["Share"] = exec_env.Share
        if len(exec_env.Activity) > 0:
            doc["Activity"] = exec_env.Activity

        # ExecutionEnvironment
        if exec_env.Platform is not None:
            doc["Platform"] = exec_env.Platform
        if exec_env.VirtualMachine is not None:
            doc["VirtualMachine"] = exec_env.VirtualMachine
        if exec_env.TotalInstances is not None:
            doc["TotalInstances"] = exec_env.TotalInstances
        if exec_env.UsedInstances is not None:
            doc["UsedInstances"] = exec_env.UsedInstances
        if exec_env.UnavailableInstances is not None:
            doc["UnavailableInstances"] = exec_env.UnavailableInstances
        if exec_env.PhysicalCPUs is not None:
            doc["PhysicalCPUs"] = exec_env.PhysicalCPUs
        if exec_env.LogicalCPUs is not None:
            doc["LogicalCPUs"] = exec_env.LogicalCPUs
        if exec_env.CPUMultiplicity is not None:
            doc["CPUMultiplicity"] = exec_env.CPUMultiplicity
        if exec_env.CPUVendor is not None:
            doc["CPUVendor"] = exec_env.CPUVendor
        if exec_env.CPUModel is not None:
            doc["CPUModel"] = exec_env.CPUModel
        if exec_env.CPUVersion is not None:
            doc["CPUVersion"] = exec_env.CPUersion
        if exec_env.CPUClockSpeed is not None:
            doc["CPUClockSpeed"] = exec_env.CPUClockSpeed
        if exec_env.CPUTimeScalingFactor is not None:
            doc["CPUTimeScalingFactor"] = exec_env.CPUTimeScalingFactor
        if exec_env.WallTimeScalingFactor is not None:
            doc["WallTimeScalingFactor"] = exec_env.WallTimeScalingFactor
        if exec_env.MainMemorySize is not None:
            doc["MainMemorySize"] = exec_env.MainMemorySize
        if exec_env.VirtualMemorySize is not None:
            doc["VirtualMemorySize"] = exec_env.VirtualMemorySize
        if exec_env.OSFamily is not None:
            doc["OSFamily"] = exec_env.OSFamily
        if exec_env.OSName is not None:
            doc["OSName"] = exec_env.OSName
        if exec_env.OSVersion is not None:
            doc["OSVersion"] = exec_env.OSVersion
        if exec_env.ConnectivityIn is not None:
            doc["ConnectivityIn"] = exec_env.ConnectivityIn
        if exec_env.ConnectivityOut is not None:
            doc["ConnectivityOut"] = exec_env.ConnectivityOut
        if exec_env.NetworkInfo is not None:
            doc["NetworkInfo"] = exec_env.NetworkInfo
        if exec_env.ComputingManager is not None:
            doc["ComputingManager"] = exec_env.ComputingManager
        if len(exec_env.ComputingShare) > 0:
            doc["ComputingShare"] = exec_env.ComputingShare
        if len(exec_env.ComputingActivity) > 0:
            doc["ComputingActivity"] = exec_env.ComputingActivity
        if len(exec_env.ApplicationEnvironment) > 0:
            doc["ApplicationEnvironment"] = exec_env.ApplicationEnvironment
        if len(exec_env.Benchmark) > 0:
            doc["Benchmark"] = self.Benchmark
            
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
        return self.toDom(self.data.exec_envs).toprettyxml()

    @staticmethod
    def toDom(exec_envs):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for exec_env in self.exec_envs:
            eedoc = ExecutionEnvironmentTeraGridXml.toDom(exec_env)
            doc.documentElement.appendChild(eedoc.documentElement.firstChild)
        return doc

#######################################################################################################################

class ExecutionEnvironmentsIpfJson(Representation):
    data_cls = ExecutionEnvironments

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data.exec_envs),sort_keys=True,indent=4)

    @staticmethod
    def toJson(shares):
        eedoc = []
        for exec_env in self.exec_envs:
            eedoc.append(ExecutionEnvironmentIpfJson.toJson(exec_env))
        return eedoc
