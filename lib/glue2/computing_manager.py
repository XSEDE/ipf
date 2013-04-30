
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

import datetime
import json
import time
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.sysinfo import ResourceName

from glue2.computing_share import ComputingShares
from glue2.execution_environment import ExecutionEnvironments
from glue2.step import GlueStep

#######################################################################################################################

class ComputingManagerStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step provides documents in the GLUE 2 ComputingManager schema. For a batch scheduled system, this is typically that scheduler."
        self.time_out = 10
        self.requires = [ResourceName,ExecutionEnvironments,ComputingShares]
        self.produces = [ComputingManager]

        self.resource_name = None
        self.exec_envs = None
        self.shares = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.exec_envs = self._getInput(ExecutionEnvironments).exec_envs
        self.shares = self._getInput(ComputingShares).shares

        manager = self._run()

        manager.id = "%s" % (self.resource_name)
        manager.ID = "urn:glue2:ComputingManager:%s" % (self.resource_name)
        manager.ComputingService = "urn:glue2:ComputingService:%s" % (self.resource_name)

        for exec_env in self.exec_envs:
            manager._addExecutionEnvironment(exec_env)
        for share in self.shares:
            manager._addComputingShare(share)

        self._output(manager)

#######################################################################################################################

class ComputingManager(Data):
    def __init__(self):
        Data.__init__(self)
        
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = None
        self.ID = None
        self.Name = None
        self.OtherInfo = []    # strings
        self.Extension = {}    # (key,value) strings

        # Manager
        self.ProductName = "unknown"    # string
        self.ProductVersion = None      # string

        # ComputingManager
        self.Version = None                      # string
        self.Reservation = None                  # boolean (ExtendedBoolean)
        self.BulkSubmission = None               # boolean (ExtendedBoolean)
        self.TotalPhysicalCPUs = None            # integer
        self.TotalLogicalCPUs = None             # integer
        self.TotalSlots = None                   # integer
        self.SlotsUsedByLocalJobs = None         # integer
        self.SlotsUsedByGridJobs = None          # integer
        self.Homogeneous = None                  # boolean (ExtendedBoolean)
        self.NetworkInfo = None                  # string (NetworkInfo)
        self.LogicalCPUDistribution = None       # string
        self.WorkingAreaShared = None            # boolean (ExtendedBoolean)
        self.WorkingAreaTotal = None             # integer
        self.WorkingAreaFree = None              # integer
        self.WorkingAreaLifeTime = None          # integer
        self.WorkingAreaMultiSlotTotal = None    # integer
        self.WorkingAreaMultiSlotFree = None     # integer
        self.WorkingAreaMultiSlotLifeTime = None # integer
        self.CacheTotal = None                   # integer
        self.CacheFree = None                    # integer
        self.TmpDir = None                       # string
        self.ScratchDir = None                   # string
        self.ApplicationDir = None               # string
        self.ComputingService = None             # string (uri)
        self.ExecutionEnvironment = []           # list of string (uri)
        self.ApplicationEnvironment = []         # list of string (LocalID)
        self.Benchmark = []                      # list of string(LocalID)

    def _addExecutionEnvironment(self, exec_env):
        self.ExecutionEnvironment.append(exec_env.ID)
        if exec_env.PhysicalCPUs != None:
            if self.TotalPhysicalCPUs == None:
                self.TotalPhysicalCPUs = 0
            self.TotalPhysicalCPUs = self.TotalPhysicalCPUs + exec_env.TotalInstances * exec_env.PhysicalCPUs
        if exec_env.LogicalCPUs != None:
            if self.TotalLogicalCPUs == None:
                self.TotalLogicalCPUs = 0
            self.TotalLogicalCPUs = self.TotalLogicalCPUs + exec_env.TotalInstances * exec_env.LogicalCPUs
            self.TotalSlots = self.TotalLogicalCPUs

        if len(self.ExecutionEnvironment) == 1:
            self.Homogeneous = True
        else:
            self.Homogeneous = False

    def _addComputingShare(self, share):
        if self.SlotsUsedByLocalJobs == None:
            self.SlotsUsedByLocalJobs = 0
        self.SlotsUsedByLocalJobs = self.SlotsUsedByLocalJobs + share.UsedSlots

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

        # Manager
        self.ProductName = doc.get("ProductName")
        self.ProductVersion = doc.get("ProductVersion")

        # ComputingManager
        self.Version = doc.get("Version")
        self.Reservation = doc.get("Reservation")
        self.BulkSubmission = doc.get("BulkSubmission")
        self.TotalPhysicalCPUs = doc.get("TotalPhysicalCPUs")
        self.TotalLogicalCPUs = doc.get("TotalLogicalCPUs")
        self.TotalSlots = doc.get("TotalSlots")
        self.SlotsUsedByLocalJobs = doc.get("SlotsUsedByLocalJobs")
        self.SlotsUsedByGridJobs = doc.get("SlotsUsedByGridJobs")
        self.Homogeneous = doc.get("Homogeneous")
        self.NetworkInfo = doc.get("NetworkInfo")
        self.LogicalCPUDistribution = doc.get("LogicalCPUDistribution")
        self.WorkingAreaShared = doc.get("WorkingAreaShared")
        self.WorkingAreaTotal = doc.get("WorkingAreaTotal")
        self.WorkingAreaFree = doc.get("WorkingAreaFree")
        self.WorkingAreaLifeTime = doc.get("WorkingAreaLifeTime")
        self.WorkingAreaMultiSlotTotal = doc.get("WorkingAreaMultiSlotTotal")
        self.WorkingAreaMultiSlotFree = doc.get("WorkingAreaMultiSlotFree")
        self.WorkingAreaMultiSlotLifeTime = doc.get("WorkingAreaMultiSlotLifeTime")
        self.CacheTotal = doc.get("CacheTotal")
        self.CacheFree = doc.get("CacheFree")
        self.TmpDir = doc.get("TmpDir")
        self.ScratchDir = doc.get("ScratchDir")
        self.ApplicationDir = doc.get("ApplicationDir")
        self.ComputingService = doc.get("ComputingService",[])
        self.ExecutionEnvironment = doc.get("ExecutionEnvironment",[])
        self.ApplicationEnvironment = doc.get("ApplicationEnvironment",[])
        self.Benchmark = doc.get("Benchmark",[])

#######################################################################################################################

class ComputingManagerTeraGridXml(Representation):
    data_cls = ComputingManager

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(manager):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingService")
        doc.documentElement.appendChild(root)

        # Entity
        root.setAttribute("CreationTime",dateTimeToText(manager.CreationTime))
        if manager.Validity is not None:
            root.setAttribute("Validity",str(manager.Validity))

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(manager.ID))
        root.appendChild(e)

        if manager.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(manager.Name))
            root.appendChild(e)
        for info in manager.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        for key in manager.Extension.keys():
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(manager.Extension[key]))
            root.appendChild(e)

        # Manager
        if manager.ProductName != None:
            e = doc.createElement("ProductName")
            e.appendChild(doc.createTextNode(manager.ProductName))
            root.appendChild(e)
        if manager.ProductVersion != None:
            e = doc.createElement("ProductVersion")
            e.appendChild(doc.createTextNode(manager.ProductVersion))
            root.appendChild(e)

        # ComputingManager
        if manager.Version != None:
            e = doc.createElement("Version")
            e.appendChild(doc.createTextNode(manager.Version))
            root.appendChild(e)
        if manager.Reservation != None:
            e = doc.createElement("Reservation")
            if manager.Reservation:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if manager.BulkSubmission != None:
            e = doc.createElement("BulkSubmission")
            if manager.BulkSubmission:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if manager.TotalPhysicalCPUs != None:
            e = doc.createElement("TotalPhysicalCPUs")
            e.appendChild(doc.createTextNode(str(manager.TotalPhysicalCPUs)))
            root.appendChild(e)
        if manager.TotalLogicalCPUs != None:
            e = doc.createElement("TotalLogicalCPUs")
            e.appendChild(doc.createTextNode(str(manager.TotalLogicalCPUs)))
            root.appendChild(e)
        if manager.TotalSlots != None:
            e = doc.createElement("TotalSlots")
            e.appendChild(doc.createTextNode(str(manager.TotalSlots)))
            root.appendChild(e)
        if manager.SlotsUsedByLocalJobs != None:
            e = doc.createElement("SlotsUsedByLocalJobs")
            e.appendChild(doc.createTextNode(str(manager.SlotsUsedByLocalJobs)))
            root.appendChild(e)
        if manager.SlotsUsedByGridJobs != None:
            e = doc.createElement("SlotsUsedByGridJobs")
            e.appendChild(doc.createTextNode(str(manager.SlotsUsedByGridJobs)))
            root.appendChild(e)
        if manager.Homogeneous != None:
            e = doc.createElement("Homogeneous")
            if manager.Homogeneous:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if manager.NetworkInfo != None:
            e = doc.createElement("NetworkInfo")
            e.appendChild(doc.createTextNode(manager.NetworkInfo))
            root.appendChild(e)
        if manager.LogicalCPUDistribution != None:
            e = doc.createElement("LogicalCPUDistribution")
            e.appendChild(doc.createTextNode(manager.LogicalCPUDistribution))
            root.appendChild(e)
        if manager.WorkingAreaShared != None:
            e = doc.createElement("WorkAreaShared")
            if manager.WorkingAreaShared:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if manager.WorkingAreaTotal != None:
            e = doc.createElement("WorkingAreaTotal")
            e.appendChild(doc.createTextNode(str(manager.WorkingAreaTotal)))
            root.appendChild(e)
        if manager.WorkingAreaFree != None:
            e = doc.createElement("WorkingAreaFree")
            e.appendChild(doc.createTextNode(str(manager.WorkingAreaFree)))
            root.appendChild(e)
        if manager.WorkingAreaLifeTime != None:
            e = doc.createElement("WorkingAreaLifeTime")
            e.appendChild(doc.createTextNode(str(manager.WorkingAreaLifeTime)))
            root.appendChild(e)
        if manager.WorkingAreaMultiSlotTotal != None:
            e = doc.createElement("WorkingAreaMultiSlotTotal")
            e.appendChild(doc.createTextNode(str(manager.WorkingAreaMultiSlotTotal)))
            root.appendChild(e)
        if manager.WorkingAreaMultiSlotFree != None:
            e = doc.createElement("WorkingAreaMultiSlotFree")
            e.appendChild(doc.createTextNode(str(manager.WorkingAreaMultiSlotFree)))
            root.appendChild(e)
        if manager.WorkingAreaMultiSlotLifeTime != None:
            e = doc.createElement("WorkingAreaMultiSlotLifeTime")
            e.appendChild(doc.createTextNode(str(manager.WorkingAreaMultiSlotLifeTime)))
            root.appendChild(e)
        if manager.CacheTotal != None:
            e = doc.createElement("CacheTotal")
            e.appendChild(doc.createTextNode(str(manager.CacheTotal)))
            root.appendChild(e)
        if manager.CacheFree != None:
            e = doc.createElement("CacheFree")
            e.appendChild(doc.createTextNode(str(manager.CacheFree)))
            root.appendChild(e)
        if manager.TmpDir != None:
            e = doc.createElement("TmpDir")
            e.appendChild(doc.createTextNode(manager.TmpDir))
            root.appendChild(e)
        if manager.ScratchDir != None:
            e = doc.createElement("ScratchDir")
            e.appendChild(doc.createTextNode(manager.ScratchDir))
            root.appendChild(e)
        if manager.ApplicationDir != None:
            e = doc.createElement("ApplicationDir")
            e.appendChild(doc.createTextNode(manager.ApplicationDir))
            root.appendChild(e)
        if manager.ComputingService != None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(manager.ComputingService))
            root.appendChild(e)
        for id in manager.ExecutionEnvironment:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for id in manager.ApplicationEnvironment:
            e = doc.createElement("ApplicationEnvironment")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for benchmark in manager.Benchmark:
            e = doc.createElement("Benchmark")
            e.appendChild(doc.createTextNode(benchmark))
            root.appendChild(e)

        return doc

#######################################################################################################################

class ComputingManagerIpfJson(Representation):
    data_cls = ComputingManager

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(manager):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(manager.CreationTime)
        if manager.Validity is not None:
            doc["Validity"] = manager.Validity
        doc["ID"] = manager.ID
        if manager.Name is not None:
            doc["Name"] = manager.Name
        if len(manager.OtherInfo) > 0:
            doc["OtherInfo"] = manager.OtherInfo
        if len(manager.Extension) > 0:
            doc["Extension"] = manager.Extension

        # Manager
        if manager.ProductName != None:
            doc["ProductName"] = manager.ProductName
        if manager.ProductVersion != None:
            doc["ProductVersion"] = manager.ProductVersion

        # ComputingManager
        if manager.Version != None:
            doc["Version"] = manager.Version
        if manager.Reservation != None:
            doc["Reservation"] = manager.Reservation
        if manager.BulkSubmission != None:
            doc["BulkSubmission"] = manager.BulkSubmission
        if manager.TotalPhysicalCPUs != None:
            doc["TotalPhysicalCPUs"] = manager.TotalPhysicalCPUs
        if manager.TotalLogicalCPUs != None:
            doc["TotalLogicalCPUs"] = manager.TotalLogicalCPUs
        if manager.TotalSlots != None:
            doc["TotalSlots"] = manager.TotalSlots
        if manager.SlotsUsedByLocalJobs != None:
            doc["SlotsUsedByLocalJobs"] = manager.SlotsUsedByLocalJobs
        if manager.SlotsUsedByGridJobs != None:
            doc["SlotsUsedByGridJobs"] = manager.SlotsUsedByGridJobs
        if manager.Homogeneous != None:
            doc["Homogeneous"] = manager.Homogeneous
        if manager.NetworkInfo != None:
            doc["NetworkInfo"] = manager.NetworkInfo
        if manager.LogicalCPUDistribution != None:
            doc["LogicalCPUDistribution"] = manager.LogicalCPUDistribution
        if manager.WorkingAreaShared != None:
            doc["WorkingAreaShared"] = manager.WorkingAreaShared
        if manager.WorkingAreaTotal != None:
            doc["WorkingAreaTotal"] = manager.WorkingAreaTotal
        if manager.WorkingAreaFree != None:
            doc["WorkingAreaFree"] = manager.WorkingAreaFree
        if manager.WorkingAreaLifeTime != None:
            doc["WorkingAreaLifeTime"] = manager.WorkingAreaLifeTime
        if manager.WorkingAreaMultiSlotTotal != None:
            doc["WorkingAreaMultiSlotTotal"] = manager.WorkingAreaMultiSlotTotal
        if manager.WorkingAreaMultiSlotFree != None:
            doc["WorkingAreaMultiSlotFree"] = manager.WorkingAreaMultiSlotFree
        if manager.WorkingAreaMultiSlotLifeTime != None:
            doc["WorkingAreaMultiSlotLifeTime"] = manager.WorkingAreaMultiSlotLifeTime
        if manager.CacheTotal != None:
            doc["CacheTotal"] = manager.CacheTotal
        if manager.CacheFree != None:
            doc["CacheFree"] = manager.CacheFree
        if manager.TmpDir != None:
            doc["TmpDir"] = manager.TmpDir
        if manager.ScratchDir != None:
            doc["ScratchDir"] = manager.ScratchDir
        if manager.ApplicationDir != None:
            doc["ApplicationDir"] = manager.ApplicationDir
        if manager.ComputingService != None:
            doc["ComputingService"] = manager.ComputingService
        if len(manager.ExecutionEnvironment) > 0:
            doc["ExecutionEnvironment"] = manager.ExecutionEnvironment
        if len(manager.ApplicationEnvironment) > 0:
            doc["ApplicationEnvironment"] = manager.ApplicationEnvironment
        if len(manager.Benchmark) > 0:
            doc["Benchmark"] = manager.Benchmark

        return doc

#######################################################################################################################
