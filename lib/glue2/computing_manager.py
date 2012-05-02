
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

import datetime
import json
import time
from xml.dom.minidom import getDOMImplementation

from ipf.document import Document
from ipf.dt import *
from ipf.step import Step

from glue2.computing_share import ComputingShare
from glue2.execution_environment import ExecutionEnvironment

#######################################################################################################################

class ComputingManagerStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "glue2/computing_manager"
        self.description = "This step provides documents in the GLUE 2 ComputingManager schema. For a batch scheduled system, this is typically that scheduler."
        self.time_out = 10
        self.requires_types = ["ipf/resource_name.txt",
                               "glue2/teragrid/execution_environments.json",
                               "glue2/teragrid/computing_shares.json"]
        self.produces_types = ["glue2/teragrid/computing_manager.xml",
                               "glue2/teragrid/computing_manager.json"]

        self.resource_name = None
        self.exec_envs = None
        self.shares = None

    def input(self, document):
        if document.type == "ipf/resource_name.txt":
            self.resource_name = document.body.rstrip()
        elif document.type == "glue2/teragrid/execution_environments.json":
            try:
                self.exec_envs = document.exec_envs
            except AttributeError:
                self.exec_envs = self._parseExecEnvsJson(document.body)
        elif document.type == "glue2/teragrid/computing_shares.json":
            try:
                self.shares = document.shares
            except AttributeError:
                self.shares = self._parseSharesJson(document.body)
        else:
            self.info("ignoring unwanted input "+document.type)

    def _parseExecEnvsJson(self, body):
        doc = json.loads(body)
        exec_envs = []
        for env_dict in doc:
            exec_env = ExecutionEnvironment()
            exec_env.fromJson(env_dict)
            exec_envs.append(exec_env)
        return exec_envs

    def _parseSharesJson(self, body):
        doc = json.loads(body)
        shares = []
        for share_dict in doc:
            share = ComputingShare()
            share.fromJson(share_dict)
            shares.append(share)
        return shares

    def run(self):
        self.info("waiting for ipf/resource_name.txt")
        while self.resource_name == None:
            time.sleep(0.25)
        self.info("waiting for glue2/teragrid/execution_environments.json")
        while self.exec_envs == None:
            time.sleep(0.25)
        self.info("waiting for glue2/teragrid/computing_shares.json")
        while self.shares == None:
            time.sleep(0.25)

        manager = self._run()

        manager.ID = "http://"+self.resource_name+"/glue2/ComputingManager"
        manager.ComputingService = "http://"+self.resource_name+"/glue2/ComputingService"

        for exec_env in self.exec_envs:
            manager._addExecutionEnvironment(exec_env)
        for share in self.shares:
            manager._addComputingShare(share)

        if "glue2/teragrid/computing_manager.xml" in self.requested_types:
            self.engine.output(self,ComputingManagerDocumentXml(self.resource_name,manager))
        if "glue2/teragrid/computing_manager.json" in self.requested_types:
            self.engine.output(self,ComputingManagerDocumentJson(self.resource_name,manager))


#######################################################################################################################

class ComputingManagerDocumentXml(Document):
    def __init__(self, resource_name, manager):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_manager.xml")
        self.manager = manager

    def _setBody(self, body):
        raise DocumentError("ComputingManagerDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        mdoc = self.manager.toDom()
        doc.documentElement.appendChild(mdoc.documentElement.firstChild)
        #return doc.toxml()
        return doc.toprettyxml()

#######################################################################################################################

class ComputingManagerDocumentJson(Document):
    def __init__(self, resource_name, manager):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_manager.json")
        self.manager = manager

    def _setBody(self, body):
        raise DocumentError("ComputingManagerDocumentJson._setBody should parse the JSON...")

    def _getBody(self):
        doc = self.manager.toJson()
        return json.dumps(doc,sort_keys=True,indent=4)

#######################################################################################################################

class ComputingManager(object):
    def __init__(self):
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = 300
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

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingService")
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
            e.appendChild(doc.createTextNode(self.Extension[key]))
            root.appendChild(e)

        # Manager
        if self.ProductName != None:
            e = doc.createElement("ProductName")
            e.appendChild(doc.createTextNode(self.ProductName))
            root.appendChild(e)
        if self.ProductVersion != None:
            e = doc.createElement("ProductVersion")
            e.appendChild(doc.createTextNode(self.ProductVersion))
            root.appendChild(e)

        # ComputingManager
        if self.Version != None:
            e = doc.createElement("Version")
            e.appendChild(doc.createTextNode(self.Version))
            root.appendChild(e)
        if self.Reservation != None:
            e = doc.createElement("Reservation")
            if self.Reservation:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.BulkSubmission != None:
            e = doc.createElement("BulkSubmission")
            if self.BulkSubmission:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.TotalPhysicalCPUs != None:
            e = doc.createElement("TotalPhysicalCPUs")
            e.appendChild(doc.createTextNode(str(self.TotalPhysicalCPUs)))
            root.appendChild(e)
        if self.TotalLogicalCPUs != None:
            e = doc.createElement("TotalLogicalCPUs")
            e.appendChild(doc.createTextNode(str(self.TotalLogicalCPUs)))
            root.appendChild(e)
        if self.TotalSlots != None:
            e = doc.createElement("TotalSlots")
            e.appendChild(doc.createTextNode(str(self.TotalSlots)))
            root.appendChild(e)
        if self.SlotsUsedByLocalJobs != None:
            e = doc.createElement("SlotsUsedByLocalJobs")
            e.appendChild(doc.createTextNode(str(self.SlotsUsedByLocalJobs)))
            root.appendChild(e)
        if self.SlotsUsedByGridJobs != None:
            e = doc.createElement("SlotsUsedByGridJobs")
            e.appendChild(doc.createTextNode(str(self.SlotsUsedByGridJobs)))
            root.appendChild(e)
        if self.Homogeneous != None:
            e = doc.createElement("Homogeneous")
            if self.Homogeneous:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.NetworkInfo != None:
            e = doc.createElement("NetworkInfo")
            e.appendChild(doc.createTextNode(self.NetworkInfo))
            root.appendChild(e)
        if self.LogicalCPUDistribution != None:
            e = doc.createElement("LogicalCPUDistribution")
            e.appendChild(doc.createTextNode(self.LogicalCPUDistribution))
            root.appendChild(e)
        if self.WorkingAreaShared != None:
            e = doc.createElement("WorkAreaShared")
            if self.WorkingAreaShared:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.WorkingAreaTotal != None:
            e = doc.createElement("WorkingAreaTotal")
            e.appendChild(doc.createTextNode(str(self.WorkingAreaTotal)))
            root.appendChild(e)
        if self.WorkingAreaFree != None:
            e = doc.createElement("WorkingAreaFree")
            e.appendChild(doc.createTextNode(str(self.WorkingAreaFree)))
            root.appendChild(e)
        if self.WorkingAreaLifeTime != None:
            e = doc.createElement("WorkingAreaLifeTime")
            e.appendChild(doc.createTextNode(str(self.WorkingAreaLifeTime)))
            root.appendChild(e)
        if self.WorkingAreaMultiSlotTotal != None:
            e = doc.createElement("WorkingAreaMultiSlotTotal")
            e.appendChild(doc.createTextNode(str(self.WorkingAreaMultiSlotTotal)))
            root.appendChild(e)
        if self.WorkingAreaMultiSlotFree != None:
            e = doc.createElement("WorkingAreaMultiSlotFree")
            e.appendChild(doc.createTextNode(str(self.WorkingAreaMultiSlotFree)))
            root.appendChild(e)
        if self.WorkingAreaMultiSlotLifeTime != None:
            e = doc.createElement("WorkingAreaMultiSlotLifeTime")
            e.appendChild(doc.createTextNode(str(self.WorkingAreaMultiSlotLifeTime)))
            root.appendChild(e)
        if self.CacheTotal != None:
            e = doc.createElement("CacheTotal")
            e.appendChild(doc.createTextNode(str(self.CacheTotal)))
            root.appendChild(e)
        if self.CacheFree != None:
            e = doc.createElement("CacheFree")
            e.appendChild(doc.createTextNode(str(self.CacheFree)))
            root.appendChild(e)
        if self.TmpDir != None:
            e = doc.createElement("TmpDir")
            e.appendChild(doc.createTextNode(self.TmpDir))
            root.appendChild(e)
        if self.ScratchDir != None:
            e = doc.createElement("ScratchDir")
            e.appendChild(doc.createTextNode(self.ScratchDir))
            root.appendChild(e)
        if self.ApplicationDir != None:
            e = doc.createElement("ApplicationDir")
            e.appendChild(doc.createTextNode(self.ApplicationDir))
            root.appendChild(e)
        if self.ComputingService != None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(self.ComputingService))
            root.appendChild(e)
        for id in self.ExecutionEnvironment:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for id in self.ApplicationEnvironment:
            e = doc.createElement("ApplicationEnvironment")
            e.appendChild(doc.createTextNode(id))
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

        # Manager
        if self.ProductName != None:
            doc["ProductName"] = self.ProductName
        if self.ProductVersion != None:
            doc["ProductVersion"] = self.ProductVersion

        # ComputingManager
        if self.Version != None:
            doc["Version"] = self.Version
        if self.Reservation != None:
            doc["Reservation"] = self.Reservation
        if self.BulkSubmission != None:
            doc["BulkSubmission"] = self.BulkSubmission
        if self.TotalPhysicalCPUs != None:
            doc["TotalPhysicalCPUs"] = self.TotalPhysicalCPUs
        if self.TotalLogicalCPUs != None:
            doc["TotalLogicalCPUs"] = self.TotalLogicalCPUs
        if self.TotalSlots != None:
            doc["TotalSlots"] = self.TotalSlots
        if self.SlotsUsedByLocalJobs != None:
            doc["SlotsUsedByLocalJobs"] = self.SlotsUsedByLocalJobs
        if self.SlotsUsedByGridJobs != None:
            doc["SlotsUsedByGridJobs"] = self.SlotsUsedByGridJobs
        if self.Homogeneous != None:
            doc["Homogeneous"] = self.Homogeneous
        if self.NetworkInfo != None:
            doc["NetworkInfo"] = self.NetworkInfo
        if self.LogicalCPUDistribution != None:
            doc["LogicalCPUDistribution"] = self.LogicalCPUDistribution
        if self.WorkingAreaShared != None:
            doc["WorkingAreaShared"] = self.WorkingAreaShared
        if self.WorkingAreaTotal != None:
            doc["WorkingAreaTotal"] = self.WorkingAreaTotal
        if self.WorkingAreaFree != None:
            doc["WorkingAreaFree"] = self.WorkingAreaFree
        if self.WorkingAreaLifeTime != None:
            doc["WorkingAreaLifeTime"] = self.WorkingAreaLifeTime
        if self.WorkingAreaMultiSlotTotal != None:
            doc["WorkingAreaMultiSlotTotal"] = self.WorkingAreaMultiSlotTotal
        if self.WorkingAreaMultiSlotFree != None:
            doc["WorkingAreaMultiSlotFree"] = self.WorkingAreaMultiSlotFree
        if self.WorkingAreaMultiSlotLifeTime != None:
            doc["WorkingAreaMultiSlotLifeTime"] = self.WorkingAreaMultiSlotLifeTime
        if self.CacheTotal != None:
            doc["CacheTotal"] = self.CacheTotal
        if self.CacheFree != None:
            doc["CacheFree"] = self.CacheFree
        if self.TmpDir != None:
            doc["TmpDir"] = self.TmpDir
        if self.ScratchDir != None:
            doc["ScratchDir"] = self.ScratchDir
        if self.ApplicationDir != None:
            doc["ApplicationDir"] = self.ApplicationDir
        if self.ComputingService != None:
            doc["ComputingService"] = self.ComputingService
        if len(self.ExecutionEnvironment) > 0:
            doc["ExecutionEnvironment"] = self.ExecutionEnvironment
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

    ###################################################################################################################

    def toXml(self, indent=""):
        mstr = indent+"<ComputingManager"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                  Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name != None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"+key+"'>"+str(self.Extension[key])+"</Extension>\n"

        # Manager
        if self.ProductName != None:
            mstr = mstr+indent+"  <ProductName>"+self.ProductName+"</ProductName>\n"
        if self.ProductVersion != None:
            mstr = mstr+indent+"  <ProductVersion>"+self.ProductVersion+"</ProductVersion>\n"

        # ComputingManager
        if self.Version != None:
            mstr = mstr+indent+"  <Version>"+self.Version+"</Version>\n"
        if self.Reservation != None:
            if self.Reservation:
                mstr = mstr+indent+"  <Reservation>true</Reservation>\n"
            else:
                mstr = mstr+indent+"  <Reservation>false</Reservation>\n"
        if self.BulkSubmission != None:
            if self.BulkSubmission:
                mstr = mstr+indent+"  <BulkSubmission>true</BulkSubmission>\n"
            else:
                mstr = mstr+indent+"  <BulkSubmission>false</BulkSubmission>\n"
        if self.TotalPhysicalCPUs != None:
            mstr = mstr+indent+"  <TotalPhysicalCPUs>"+str(self.TotalPhysicalCPUs)+"</TotalPhysicalCPUs>\n"
        if self.TotalLogicalCPUs != None:
            mstr = mstr+indent+"  <TotalLogicalCPUs>"+str(self.TotalLogicalCPUs)+"</TotalLogicalCPUs>\n"
        if self.TotalSlots != None:
            mstr = mstr+indent+"  <TotalSlots>"+str(self.TotalSlots)+"</TotalSlots>\n"
        if self.SlotsUsedByLocalJobs != None:
            mstr = mstr+indent+"  <SlotsUsedByLocalJobs>"+str(self.SlotsUsedByLocalJobs)+"</SlotsUsedByLocalJobs>\n"
        if self.SlotsUsedByGridJobs != None:
            mstr = mstr+indent+"  <SlotsUsedByGridJobs>"+str(self.SlotsUsedByGridJobs)+"</SlotsUsedByGridJobs>\n"
        if self.Homogeneous != None:
            if self.Homogeneous:
                mstr = mstr+indent+"  <Homogeneous>true</Homogeneous>\n"
            else:
                mstr = mstr+indent+"  <Homogeneous>false</Homogeneous>\n"
        if self.NetworkInfo != None:
            mstr = mstr+indent+"  <NetworkInfo>"+self.NetworkInfo+"</NetworkInfo>\n"
        if self.LogicalCPUDistribution != None:
            mstr = mstr+indent+"  <LogicalCPUDistribution>"+str(self.LogicalCPUDistribution)+ \
                   "</LogicalCPUDistribution>\n"
        if self.WorkingAreaShared != None:
            if self.WorkingAreaShared:
                mstr = mstr+indent+"  <WorkingAreaShared>true</WorkingAreaShared>\n"
            else:
                mstr = mstr+indent+"  <WorkingAreaShared>false</WorkingAreaShared>\n"
        if self.WorkingAreaTotal != None:
            mstr = mstr+indent+"  <WorkingAreaTotal>"+str(self.WorkingAreaTotal)+"</WorkingAreaTotal>\n"
        if self.WorkingAreaFree != None:
            mstr = mstr+indent+"  <WorkingAreaFree>"+str(self.WorkingAreaFree)+"</WorkingAreaFree>\n"
        if self.WorkingAreaLifeTime != None:
            mstr = mstr+indent+"  <WorkingAreaLifeTime>"+str(self.WorkingAreaLifeTime)+"</WorkingAreaLifeTime>\n"
        if self.WorkingAreaMultiSlotTotal != None:
            mstr = mstr+indent+"  <WorkingAreaMultiSlotTotal>"+str(self.WorkingAreaMultiSlotTotal)+ \
                   "</WorkingAreaMultiSLotTotal>\n"
        if self.WorkingAreaMultiSlotFree != None:
            mstr = mstr+indent+"  <WorkingAreaFMultiSlotree>"+str(self.WorkingAreaMultiSlotFree)+ \
                   "</WorkingAreaMultiSlotFree>\n"
        if self.WorkingAreaMultiSlotLifeTime != None:
            mstr = mstr+indent+"  <WorkingAreaMultiSlotLifeTime>"+str(self.WorkingAreaMultiSlotLifeTime)+ \
                   "</WorkingMultiSlotAreaLifeTime>\n"
        if self.CacheTotal != None:
            mstr = mstr+indent+"  <CacheTotal>"+str(self.CacheTotal)+"</CacheTotal>\n"
        if self.CacheFree != None:
            mstr = mstr+indent+"  <CacheFree>"+str(self.CacheFree)+"</CacheFree>\n"
        if self.TmpDir != None:
            mstr = mstr+indent+"  <TmpDir>"+self.TmpDir+"</TmpDir>\n"
        if self.ScratchDir != None:
            mstr = mstr+indent+"  <ScratchDir>"+self.ScratchDir+"</ScratchDir>\n"
        if self.ApplicationDir != None:
            mstr = mstr+indent+"  <ApplicationDir>"+self.ApplicationDir+"</ApplicationDir>\n"
        if self.ComputingService != None:
            mstr = mstr+indent+"  <ComputingService>"+self.ComputingService+"</ComputingService>\n"
        for id in self.ExecutionEnvironment:
            mstr = mstr+indent+"  <ExecutionEnvironment>"+id+"</ExecutionEnvironment>\n"
        for appEnv in self.ApplicationEnvironment:
            mstr = mstr+indent+"  <ApplicationEnvironment>"+appEnv+"</ApplicationEnvironment>\n"
        for benchmark in self.Benchmark:
            mstr = mstr+indent+"  <Benchmark>"+benchmark+"</Benchmark>\n"
        mstr = mstr+indent+"</ComputingManager>\n"

        return mstr
