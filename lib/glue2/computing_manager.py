
###############################################################################
#   Copyright 2011-2013 The University of Texas at Austin                     #
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
from glue2.manager import *
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
        manager.Service = "urn:glue2:ComputingService:%s" % (self.resource_name)

        for exec_env in self.exec_envs:
            manager._addExecutionEnvironment(exec_env)
        for share in self.shares:
            manager._addComputingShare(share)

        self._output(manager)

#######################################################################################################################

class ComputingManager(Manager):
    def __init__(self):
        Manager.__init__(self)

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
        # use Service and Resource of Manager instead of ComputingService and ExecutionEnvironment
        self.ApplicationEnvironment = []         # list of string (LocalID)
        self.Benchmark = []                      # list of string(LocalID)

    def _addExecutionEnvironment(self, exec_env):
        self.Resource.append(exec_env.ID)
        if exec_env.PhysicalCPUs != None:
            if self.TotalPhysicalCPUs == None:
                self.TotalPhysicalCPUs = 0
            self.TotalPhysicalCPUs = self.TotalPhysicalCPUs + exec_env.TotalInstances * exec_env.PhysicalCPUs
        if exec_env.LogicalCPUs != None:
            if self.TotalLogicalCPUs == None:
                self.TotalLogicalCPUs = 0
            self.TotalLogicalCPUs = self.TotalLogicalCPUs + exec_env.TotalInstances * exec_env.LogicalCPUs
            self.TotalSlots = self.TotalLogicalCPUs

        if len(self.Resource) == 1:
            self.Homogeneous = True
        else:
            self.Homogeneous = False

    def _addComputingShare(self, share):
        if self.SlotsUsedByLocalJobs == None:
            self.SlotsUsedByLocalJobs = 0
        self.SlotsUsedByLocalJobs = self.SlotsUsedByLocalJobs + share.UsedSlots

#######################################################################################################################

class ComputingManagerTeraGridXml(ManagerTeraGridXml):
    data_cls = ComputingManager

    def __init__(self, data):
        ManagerTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingManager")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        ManagerTeraGridXml.addToDomElement(self,doc,element)

        if self.data.Version != None:
            e = doc.createElement("Version")
            e.appendChild(doc.createTextNode(self.data.Version))
            element.appendChild(e)
        if self.data.Reservation != None:
            e = doc.createElement("Reservation")
            if self.data.Reservation:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.BulkSubmission != None:
            e = doc.createElement("BulkSubmission")
            if self.data.BulkSubmission:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.TotalPhysicalCPUs != None:
            e = doc.createElement("TotalPhysicalCPUs")
            e.appendChild(doc.createTextNode(str(self.data.TotalPhysicalCPUs)))
            element.appendChild(e)
        if self.data.TotalLogicalCPUs != None:
            e = doc.createElement("TotalLogicalCPUs")
            e.appendChild(doc.createTextNode(str(self.data.TotalLogicalCPUs)))
            element.appendChild(e)
        if self.data.TotalSlots != None:
            e = doc.createElement("TotalSlots")
            e.appendChild(doc.createTextNode(str(self.data.TotalSlots)))
            element.appendChild(e)
        if self.data.SlotsUsedByLocalJobs != None:
            e = doc.createElement("SlotsUsedByLocalJobs")
            e.appendChild(doc.createTextNode(str(self.data.SlotsUsedByLocalJobs)))
            element.appendChild(e)
        if self.data.SlotsUsedByGridJobs != None:
            e = doc.createElement("SlotsUsedByGridJobs")
            e.appendChild(doc.createTextNode(str(self.data.SlotsUsedByGridJobs)))
            element.appendChild(e)
        if self.data.Homogeneous != None:
            e = doc.createElement("Homogeneous")
            if self.data.Homogeneous:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.NetworkInfo != None:
            e = doc.createElement("NetworkInfo")
            e.appendChild(doc.createTextNode(self.data.NetworkInfo))
            element.appendChild(e)
        if self.data.LogicalCPUDistribution != None:
            e = doc.createElement("LogicalCPUDistribution")
            e.appendChild(doc.createTextNode(self.data.LogicalCPUDistribution))
            element.appendChild(e)
        if self.data.WorkingAreaShared != None:
            e = doc.createElement("WorkAreaShared")
            if self.data.WorkingAreaShared:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.WorkingAreaTotal != None:
            e = doc.createElement("WorkingAreaTotal")
            e.appendChild(doc.createTextNode(str(self.data.WorkingAreaTotal)))
            element.appendChild(e)
        if self.data.WorkingAreaFree != None:
            e = doc.createElement("WorkingAreaFree")
            e.appendChild(doc.createTextNode(str(self.data.WorkingAreaFree)))
            element.appendChild(e)
        if self.data.WorkingAreaLifeTime != None:
            e = doc.createElement("WorkingAreaLifeTime")
            e.appendChild(doc.createTextNode(str(self.data.WorkingAreaLifeTime)))
            element.appendChild(e)
        if self.data.WorkingAreaMultiSlotTotal != None:
            e = doc.createElement("WorkingAreaMultiSlotTotal")
            e.appendChild(doc.createTextNode(str(self.data.WorkingAreaMultiSlotTotal)))
            element.appendChild(e)
        if self.data.WorkingAreaMultiSlotFree != None:
            e = doc.createElement("WorkingAreaMultiSlotFree")
            e.appendChild(doc.createTextNode(str(self.data.WorkingAreaMultiSlotFree)))
            element.appendChild(e)
        if self.data.WorkingAreaMultiSlotLifeTime != None:
            e = doc.createElement("WorkingAreaMultiSlotLifeTime")
            e.appendChild(doc.createTextNode(str(self.data.WorkingAreaMultiSlotLifeTime)))
            element.appendChild(e)
        if self.data.CacheTotal != None:
            e = doc.createElement("CacheTotal")
            e.appendChild(doc.createTextNode(str(self.data.CacheTotal)))
            element.appendChild(e)
        if self.data.CacheFree != None:
            e = doc.createElement("CacheFree")
            e.appendChild(doc.createTextNode(str(self.data.CacheFree)))
            element.appendChild(e)
        if self.data.TmpDir != None:
            e = doc.createElement("TmpDir")
            e.appendChild(doc.createTextNode(self.data.TmpDir))
            element.appendChild(e)
        if self.data.ScratchDir != None:
            e = doc.createElement("ScratchDir")
            e.appendChild(doc.createTextNode(self.data.ScratchDir))
            element.appendChild(e)
        if self.data.ApplicationDir != None:
            e = doc.createElement("ApplicationDir")
            e.appendChild(doc.createTextNode(self.data.ApplicationDir))
            element.appendChild(e)
        if self.data.Service != None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(self.data.Service))
            element.appendChild(e)
        for id in self.data.Resource:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for id in self.data.ApplicationEnvironment:
            e = doc.createElement("ApplicationEnvironment")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for benchmark in self.data.Benchmark:
            e = doc.createElement("Benchmark")
            e.appendChild(doc.createTextNode(benchmark))
            element.appendChild(e)

#######################################################################################################################

class ComputingManagerOgfJson(ManagerOgfJson):
    data_cls = ComputingManager

    def __init__(self, data):
        ManagerOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = ManagerOgfJson.toJson(self)

        if self.data.Version != None:
            doc["Version"] = self.data.Version
        if self.data.Reservation != None:
            doc["Reservation"] = self.data.Reservation
        if self.data.BulkSubmission != None:
            doc["BulkSubmission"] = self.data.BulkSubmission
        if self.data.TotalPhysicalCPUs != None:
            doc["TotalPhysicalCPUs"] = self.data.TotalPhysicalCPUs
        if self.data.TotalLogicalCPUs != None:
            doc["TotalLogicalCPUs"] = self.data.TotalLogicalCPUs
        if self.data.TotalSlots != None:
            doc["TotalSlots"] = self.data.TotalSlots
        if self.data.SlotsUsedByLocalJobs != None:
            doc["SlotsUsedByLocalJobs"] = self.data.SlotsUsedByLocalJobs
        if self.data.SlotsUsedByGridJobs != None:
            doc["SlotsUsedByGridJobs"] = self.data.SlotsUsedByGridJobs
        if self.data.Homogeneous != None:
            doc["Homogeneous"] = self.data.Homogeneous
        if self.data.NetworkInfo != None:
            doc["NetworkInfo"] = self.data.NetworkInfo
        if self.data.LogicalCPUDistribution != None:
            doc["LogicalCPUDistribution"] = self.data.LogicalCPUDistribution
        if self.data.WorkingAreaShared != None:
            doc["WorkingAreaShared"] = self.data.WorkingAreaShared
        if self.data.WorkingAreaTotal != None:
            doc["WorkingAreaTotal"] = self.data.WorkingAreaTotal
        if self.data.WorkingAreaFree != None:
            doc["WorkingAreaFree"] = self.data.WorkingAreaFree
        if self.data.WorkingAreaLifeTime != None:
            doc["WorkingAreaLifeTime"] = self.data.WorkingAreaLifeTime
        if self.data.WorkingAreaMultiSlotTotal != None:
            doc["WorkingAreaMultiSlotTotal"] = self.data.WorkingAreaMultiSlotTotal
        if self.data.WorkingAreaMultiSlotFree != None:
            doc["WorkingAreaMultiSlotFree"] = self.data.WorkingAreaMultiSlotFree
        if self.data.WorkingAreaMultiSlotLifeTime != None:
            doc["WorkingAreaMultiSlotLifeTime"] = self.data.WorkingAreaMultiSlotLifeTime
        if self.data.CacheTotal != None:
            doc["CacheTotal"] = self.data.CacheTotal
        if self.data.CacheFree != None:
            doc["CacheFree"] = self.data.CacheFree
        if self.data.TmpDir != None:
            doc["TmpDir"] = self.data.TmpDir
        if self.data.ScratchDir != None:
            doc["ScratchDir"] = self.data.ScratchDir
        if self.data.ApplicationDir != None:
            doc["ApplicationDir"] = self.data.ApplicationDir
        if len(self.data.ApplicationEnvironment) > 0:
            doc["ApplicationEnvironment"] = self.data.ApplicationEnvironment
        if len(self.data.Benchmark) > 0:
            doc["Benchmark"] = self.data.Benchmark

        return doc

#######################################################################################################################
