
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
import copy
import datetime
import json
import os
import socket
import time
from xml.dom.minidom import getDOMImplementation

from ipf.document import Document
from ipf.dt import *
from ipf.error import StepError

from glue2.step import GlueStep

#######################################################################################################################

class ExecutionEnvironmentsStep(GlueStep):
    name = "glue2/execution_environments"
    description = "Produces a document containing one or more GLUE 2 ExecutionEnvironment. For a batch scheduled system, an ExecutionEnivonment is typically a compute node."
    time_out = 30
    requires_types = ["ipf/resource_name.txt",
                      "teragrid/platform.txt"]
    produces_types = ["glue2/teragrid/execution_environments.xml",
                      "glue2/teragrid/execution_environments.json"]
    accepts_params = copy.copy(GlueStep.accepts_params)
    accepts_params["queues"] = "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. the expression is processed in order and the value for a queue at the end determines if it is shown."

    def __init__(self, params):
        GlueStep.__init__(self,params)
        self.resource_name = None
        self.platform = None

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        self.resource_name = rn_doc.resource_name
        platform_doc = self._getInput("teragrid/platform.txt")
        self.platform = platform_doc.platform
        
        hosts = self._run()
        host_groups = self._groupHosts(hosts)

        for index in range(0,len(host_groups)):
            host_groups[index].Name = "NodeType%d" % (index+1)
            host_groups[index].ID = "http://%s/glue2/ExecutionEnvironment/%s" % \
                                    (self.resource_name,host_groups[index].Name)
        for host_group in host_groups:
            #host_group.id = host_group.Name+"."+self.resource_name
            host_group.Extension["TeraGridPlatform"] = self.platform

        if "glue2/teragrid/execution_environments.xml" in self.requested_types:
            self.debug("sending output glue2/teragrid/execution_environment.xml")
            self.output_queue.put(ExecutionEnvironmentsDocumentXml(self.resource_name,host_groups))
        if "glue2/teragrid/execution_environments.json" in self.requested_types:
            self.debug("sending output glue2/teragrid/execution_environment.json")
            self.output_queue.put(ExecutionEnvironmentsDocumentJson(self.resource_name,host_groups))

    def _groupHosts(self, hosts):
        host_groups = []
        for host in hosts:
            for host_group in host_groups:
                if host.sameHostGroup(host_group):
                    if "UsedAverageLoad" in host.Extension:
                        host_load = host.Extension["UsedAverageLoad"]
                        if not "UsedAverageLoad" in host_group.Extension:
                            host_group.Extension["UsedAverageLoad"] = host_load
                        else:
                            host_group_load = host_group.Extension["UsedAverageLoad"]
                            host_group_load = (host_group_load * host_group.UsedInstances +
                                               host_load * host.UsedInstances) / \
                                               (host_group.UsedInstances + host.UsedInstances)
                            host_group.Extension["UsedAverageLoad"] = host_group_load
                    if "AvailableAverageLoad" in host.Extension:
                        host_load = host.Extension["AvailableAverageLoad"]
                        if not "AvailableAverageLoad" in host_group.Extension:
                            host_group.Extension["AvailableAverageLoad"] = host_load
                        else:
                            host_group_load = host_group.Extension["AvailableAverageLoad"]
                            host_group_avail = host_group.TotalInstances - host_group.UsedInstances - \
                                               host_group.UnavailableInstances
                            host_avail = host.TotalInstances - host.UsedInstances - host.UnavailableInstances
                            host_group_load = (host_group_load * host_group_avail +
                                               host_load * host_avail) / \
                                               (host_group_avail + host_group_avail)
                            host_group.Extension["AvailableAverageLoad"] = host_group_load
                    host_group.TotalInstances += host.TotalInstances
                    host_group.UsedInstances += host.UsedInstances
                    host_group.UnavailableInstances += host.UnavailableInstances
                    host = None
                    break
            if host is not None:
                host_groups.append(host)

        return host_groups

    def _run(self):
        self.error("ExecutionEnvironmentsStep._run not overriden")
        raise StepError("ExecutionEnvironmentsStep._run not overriden")

    def _goodHost(self, host):
        # check that it has cpu information
        if host.PhysicalCPUs == None:
            return False

        # check that it is associated with a good queue
        for queue in host.ComputingShare:
            if self._includeQueue(queue):
                return True
        return False


#######################################################################################################################

class ExecutionEnvironmentsDocumentXml(Document):
    def __init__(self, resource_name, exec_envs):
        Document.__init__(self, resource_name, "glue2/teragrid/execution_environments.xml")
        self.exec_envs = exec_envs

    def _setBody(self, body):
        raise DocumentError("ExecutionEnvironmentsXml._setBody should parse the XML...")

    def _getBody(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for exec_env in self.exec_envs:
            eedoc = exec_env.toDom()
            doc.documentElement.appendChild(eedoc.documentElement.firstChild)
        #return doc.toxml()
        return doc.toprettyxml()

#######################################################################################################################

class ExecutionEnvironmentsDocumentJson(Document):
    def __init__(self, resource_name, exec_envs):
        Document.__init__(self, resource_name, "glue2/teragrid/execution_environments.json")
        self.exec_envs = exec_envs

    def _setBody(self, body):
        raise DocumentError("ExecutionEnvironmentsJson._setBody should parse the JSON...")

    def _getBody(self):
        eedoc = []
        for exec_env in self.exec_envs:
            eedoc.append(exec_env.toJson())
        return json.dumps(eedoc,sort_keys=True,indent=4)

#######################################################################################################################

class ExecutionEnvironment(object):
    def __init__(self):
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = 300
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

    def sameHostGroup(self, execEnv):
        if self.Platform != execEnv.Platform:
            return False
        if self.PhysicalCPUs != execEnv.PhysicalCPUs:
            return False
        if self.LogicalCPUs != execEnv.LogicalCPUs:
            return False
        if self.CPUVendor != execEnv.CPUVendor:
            return False
        if self.CPUModel != execEnv.CPUModel:
            return False
        if self.CPUVersion != execEnv.CPUVersion:
            return False
        if self.CPUClockSpeed != execEnv.CPUClockSpeed:
            return False
        if self.MainMemorySize != execEnv.MainMemorySize:
            return False
        #if self.VirtualMemorySize != execEnv.VirtualMemorySize:
        #    return False
        if self.OSFamily != execEnv.OSFamily:
            return False
        if self.OSName != execEnv.OSName:
            return False
        if self.OSVersion != execEnv.OSVersion:
            return False

        if len(self.ComputingShare) != len(execEnv.ComputingShare):
            return False
        for share in self.ComputingShare:
            if not share in execEnv.ComputingShare:
                return False

        return True
    
    ###################################################################################################################

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ExecutionEnvironment")
        doc.documentElement.appendChild(root)

        # Entity
        e = doc.createElement("CreationTime")
        e.appendChild(doc.createTextNode(dateTimeToText(self.CreationTime)))
        e.setAttribute("Validity",str(self.Validity))
        root.appendChild(e)

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(self.ID))
        root.appendChild(e)

        if self.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(self.Name))
            root.appendChild(e)
        for info in self.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        for key in self.Extension.keys():
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(str(self.Extension[key])))
            root.appendChild(e)

        # Resource
        if self.Manager is not None:
            e = doc.createElement("Manager")
            e.appendChild(doc.createTextNode(self.Manager))
            root.appendChild(e)
        for share in self.Share:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for activity in self.Activity:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(self.Activity))
            root.appendChild(e)

        # ExecutionEnvironment
        if self.Platform is not None:
            e = doc.createElement("Platform")
            e.appendChild(doc.createTextNode(self.Platform))
            root.appendChild(e)
        if self.VirtualMachine is not None:
            e = doc.createElement("VirtualMachine")
            if self.VirtualMachine:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.TotalInstances is not None:
            e = doc.createElement("TotalInstances")
            e.appendChild(doc.createTextNode(str(self.TotalInstances)))
            root.appendChild(e)
        if self.UsedInstances is not None:
            e = doc.createElement("UsedInstances")
            e.appendChild(doc.createTextNode(str(self.UsedInstances)))
            root.appendChild(e)
        if self.UnavailableInstances is not None:
            e = doc.createElement("UnavailableInstances")
            e.appendChild(doc.createTextNode(str(self.UnavailableInstances)))
            root.appendChild(e)
        if self.PhysicalCPUs is not None:
            e = doc.createElement("PhysicalCPUs")
            e.appendChild(doc.createTextNode(str(self.PhysicalCPUs)))
            root.appendChild(e)
        if self.LogicalCPUs is not None:
            e = doc.createElement("LogicalCPUs")
            e.appendChild(doc.createTextNode(str(self.LogicalCPUs)))
            root.appendChild(e)
        if self.CPUMultiplicity is not None:
            e = doc.createElement("CPUMultiplicity")
            e.appendChild(doc.createTextNode(self.CPUMultiplicity))
            root.appendChild(e)
        if self.CPUVendor is not None:
            e = doc.createElement("CPUVendor")
            e.appendChild(doc.createTextNode(self.CPUVendor))
            root.appendChild(e)
        if self.CPUModel is not None:
            e = doc.createElement("CPUModel")
            e.appendChild(doc.createTextNode(self.CPUModel))
            root.appendChild(e)
        if self.CPUVersion is not None:
            e = doc.createElement("CPUVersion")
            e.appendChild(doc.createTextNode(self.CPUVersion))
            root.appendChild(e)
        if self.CPUClockSpeed is not None:
            e = doc.createElement("CPUClockSpeed")
            e.appendChild(doc.createTextNode(str(self.CPUClockSpeed)))
            root.appendChild(e)
        if self.CPUTimeScalingFactor is not None:
            e = doc.createElement("CPUTimeScalingFactor")
            e.appendChild(doc.createTextNode(str(self.CPUTimeScalingFactor)))
            root.appendChild(e)
        if self.WallTimeScalingFactor is not None:
            e = doc.createElement("WallTimeScalingFactor")
            e.appendChild(doc.createTextNode(str(self.WallTimeScalingFactor)))
            root.appendChild(e)
        if self.MainMemorySize is not None:
            e = doc.createElement("MainMemorySize")
            e.appendChild(doc.createTextNode(str(self.MainMemorySize)))
            root.appendChild(e)
        if self.VirtualMemorySize is not None:
            e = doc.createElement("VirtualMemorySize")
            e.appendChild(doc.createTextNode(str(self.VirtualMemorySize)))
            root.appendChild(e)
        if self.OSFamily is not None:
            e = doc.createElement("OSFamily")
            e.appendChild(doc.createTextNode(self.OSFamily))
            root.appendChild(e)
        if self.OSName is not None:
            e = doc.createElement("OSName")
            e.appendChild(doc.createTextNode(self.OSName))
            root.appendChild(e)
        if self.OSVersion is not None:
            e = doc.createElement("OSVersion")
            e.appendChild(doc.createTextNode(self.OSVersion))
            root.appendChild(e)
        if self.ConnectivityIn == None:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("undefined"))
            root.appendChild(e)
        elif self.ConnectivityIn:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("true"))
            root.appendChild(e)
        else:
            e = doc.createElement("ConnectivityIn")
            e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.ConnectivityOut == None:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("undefined"))
            root.appendChild(e)
        elif self.ConnectivityOut:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("true"))
            root.appendChild(e)
        else:
            e = doc.createElement("ConnectivityOut")
            e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.NetworkInfo is not None:
            e = doc.createElement("NetworkInfo")
            e.appendChild(doc.createTextNode(self.NetworkInfo))
            root.appendChild(e)
        if self.ComputingManager is not None:
            e = doc.createElement("ComputingManager")
            e.appendChild(doc.createTextNode(self.ComputingManager))
            root.appendChild(e)
        for share in self.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for activity in self.ComputingActivity:
            e = doc.createElement("ComputingActivity")
            e.appendChild(doc.createTextNode(activity))
            root.appendChild(e)
        for appEnv in self.ApplicationEnvironment:
            e = doc.createElement("ApplicationEnvironment")
            e.appendChild(doc.createTextNode(appEnv))
            root.appendChild(e)
        for benchmark in self.Benchmark:
            e = doc.createElement("Benchmark")
            e.appendChild(doc.createTextNode(benchmark))
            root.appendChild(e)
            
        return doc
    
    ###################################################################################################################

    def toJson(self):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(self.CreationTime)
        doc["Validity"] = self.Validity
        doc["ID"] = self.ID
        if self.Name is not None:
            doc["Name"] = self.Name
        if len(self.OtherInfo) > 0:
            doc["OtherInfo"] = self.OtherInfo
        if len(self.Extension) > 0:
            doc["Extension"] = self.Extension

        # Resource
        if self.Manager is not None:
            doc["Manager"] = self.Manager
        if len(self.Share) > 0:
            doc["Share"] = self.Share
        if len(self.Activity) > 0:
            doc["Activity"] = self.Activity

        # ExecutionEnvironment
        if self.Platform is not None:
            doc["Platform"] = self.Platform
        if self.VirtualMachine is not None:
            doc["VirtualMachine"] = self.VirtualMachine
        if self.TotalInstances is not None:
            doc["TotalInstances"] = self.TotalInstances
        if self.UsedInstances is not None:
            doc["UsedInstances"] = self.UsedInstances
        if self.UnavailableInstances is not None:
            doc["UnavailableInstances"] = self.UnavailableInstances
        if self.PhysicalCPUs is not None:
            doc["PhysicalCPUs"] = self.PhysicalCPUs
        if self.LogicalCPUs is not None:
            doc["LogicalCPUs"] = self.LogicalCPUs
        if self.CPUMultiplicity is not None:
            doc["CPUMultiplicity"] = self.CPUMultiplicity
        if self.CPUVendor is not None:
            doc["CPUVendor"] = self.CPUVendor
        if self.CPUModel is not None:
            doc["CPUModel"] = self.CPUModel
        if self.CPUVersion is not None:
            doc["CPUVersion"] = self.CPUersion
        if self.CPUClockSpeed is not None:
            doc["CPUClockSpeed"] = self.CPUClockSpeed
        if self.CPUTimeScalingFactor is not None:
            doc["CPUTimeScalingFactor"] = self.CPUTimeScalingFactor
        if self.WallTimeScalingFactor is not None:
            doc["WallTimeScalingFactor"] = self.WallTimeScalingFactor
        if self.MainMemorySize is not None:
            doc["MainMemorySize"] = self.MainMemorySize
        if self.VirtualMemorySize is not None:
            doc["VirtualMemorySize"] = self.VirtualMemorySize
        if self.OSFamily is not None:
            doc["OSFamily"] = self.OSFamily
        if self.OSName is not None:
            doc["OSName"] = self.OSName
        if self.OSVersion is not None:
            doc["OSVersion"] = self.OSVersion
        if self.ConnectivityIn is not None:
            doc["ConnectivityIn"] = self.ConnectivityIn
        if self.ConnectivityOut is not None:
            doc["ConnectivityOut"] = self.ConnectivityOut
        if self.NetworkInfo is not None:
            doc["NetworkInfo"] = self.NetworkInfo
        if self.ComputingManager is not None:
            doc["ComputingManager"] = self.ComputingManager
        if len(self.ComputingShare) > 0:
            doc["ComputingShare"] = self.ComputingShare
        if len(self.ComputingActivity) > 0:
            doc["ComputingActivity"] = self.ComputingActivity
        if len(self.ApplicationEnvironment) > 0:
            doc["ApplicationEnvironment"] = self.ApplicationEnvironment
        if len(self.Benchmark) > 0:
            doc["Benchmark"] = self.Benchmark
            
        return doc
    
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
    
    ###################################################################################################################

    def toXml(self, indent=""):
        mstr = indent+"<ExecutionEnvironment"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                      Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+str(self.ID)+"</ID>\n"
        if self.Name is not None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"+key+"'>"+str(self.Extension[key])+"</Extension>\n"

        # Resource
        if self.Manager is not None:
            mstr = mstr+indent+"  <Manager>"+self.Manager+"</Manager>\n"
        for share in self.Share:
            mstr = mstr+indent+"  <Share>"+share+"</Share>\n"
        for activity in self.Activity:
            mstr = mstr+indent+"  <Activity>"+activity+"</Activity>\n"

        # ExecutionEnvironment
        if self.Platform is not None:
            mstr = mstr+indent+"  <Platform>"+self.Platform+"</Platform>\n"
        if self.VirtualMachine is not None:
            if self.VirtualMachine:
                mstr = mstr+indent+"  <VirtualMachine>true</VirtualMachine>\n"
            else:
                mstr = mstr+indent+"  <VirtualMachine>false</VirtualMachine>\n"
        if self.TotalInstances is not None:
            mstr = mstr+indent+"  <TotalInstances>"+str(self.TotalInstances)+"</TotalInstances>\n"
        if self.UsedInstances is not None:
            mstr = mstr+indent+"  <UsedInstances>"+str(self.UsedInstances)+"</UsedInstances>\n"
        if self.UnavailableInstances is not None:
            mstr = mstr+indent+"  <UnavailableInstances>"+str(self.UnavailableInstances)+"</UnavailableInstances>\n"
        if self.PhysicalCPUs is not None:
            mstr = mstr+indent+"  <PhysicalCPUs>"+str(self.PhysicalCPUs)+"</PhysicalCPUs>\n"
        if self.LogicalCPUs is not None:
            mstr = mstr+indent+"  <LogicalCPUs>"+str(self.LogicalCPUs)+"</LogicalCPUs>\n"
        if self.CPUMultiplicity is not None:
            mstr = mstr+indent+"  <CPUMultiplicity>"+self.CPUMultiplicity+"</CPUMultiplicity>\n"
        if self.CPUVendor is not None:
            mstr = mstr+indent+"  <CPUVendor>"+self.CPUVendor+"</CPUVendor>\n"
        if self.CPUModel is not None:
            mstr = mstr+indent+"  <CPUModel>"+self.CPUModel+"</CPUModel>\n"
        if self.CPUVersion is not None:
            mstr = mstr+indent+"  <CPUVersion>"+self.CPUVersion+"</CPUVersion>\n"
        if self.CPUClockSpeed is not None:
            mstr = mstr+indent+"  <CPUClockSpeed>"+str(self.CPUClockSpeed)+"</CPUClockSpeed>\n"
        if self.CPUTimeScalingFactor is not None:
            mstr = mstr+indent+"  <CPUTimeScalingFactor>"+str(self.CPUTimeScalingFactor)+"</CPUTimeScalingFactor>\n"
        if self.WallTimeScalingFactor is not None:
            mstr = mstr+indent+"  <WallTimeScalingFactor>"+str(self.WallTimeScalingFactor)+"</WallTimeScalingFactor>\n"
        if self.MainMemorySize is not None:
            mstr = mstr+indent+"  <MainMemorySize>"+str(self.MainMemorySize)+"</MainMemorySize>\n"
        if self.VirtualMemorySize is not None:
            mstr = mstr+indent+"  <VirtualMemorySize>"+str(self.VirtualMemorySize)+"</VirtualMemorySize>\n"
        if self.OSFamily is not None:
            mstr = mstr+indent+"  <OSFamily>"+self.OSFamily+"</OSFamily>\n"
        if self.OSName is not None:
            mstr = mstr+indent+"  <OSName>"+self.OSName+"</OSName>\n"
        if self.OSVersion is not None:
            mstr = mstr+indent+"  <OSVersion>"+self.OSVersion+"</OSVersion>\n"
        if self.ConnectivityIn == None:
            mstr = mstr+indent+"  <ConnectivityIn>undefined</ConnectivityIn>\n"
        elif self.ConnectivityIn:
            mstr = mstr+indent+"  <ConnectivityIn>true</ConnectivityIn>\n"
        else:
            mstr = mstr+indent+"  <ConnectivityIn>false</ConnectivityIn>\n"
        if self.ConnectivityOut == None:
            mstr = mstr+indent+"  <ConnectivityOut>undefined</ConnectivityOut>\n"
        elif self.ConnectivityOut:
            mstr = mstr+indent+"  <ConnectivityOut>true</ConnectivityOut>\n"
        else:
            mstr = mstr+indent+"  <ConnectivityOut>false</ConnectivityOut>\n"
        if self.NetworkInfo is not None:
            mstr = mstr+indent+"  <NetworkInfo>"+self.NetworkInfo+"</NetworkInfo>\n"
        if self.ComputingManager is not None:
            mstr = mstr+indent+"  <ComputingManager>"+self.ComputingManager+"</ComputingManager>\n"
        for share in self.ComputingShare:
            mstr = mstr+indent+"  <ComputingShare>"+share+"</ComputingShare>\n"
        for activity in self.ComputingActivity:
            mstr = mstr+indent+"  <ComputingActivity>"+activity+"</ComputingActivity>\n"
        for appEnv in self.ApplicationEnvironment:
            mstr = mstr+indent+"  <ApplicationEnvironment>"+appEnv+"</ApplicationEnvironment>\n"
        for benchmark in self.Benchmark:
            mstr = mstr+indent+"  <Benchmark>"+benchmark+"</Benchmark>\n"
        mstr = mstr+indent+"</ExecutionEnvironment>\n"
            
        return mstr
