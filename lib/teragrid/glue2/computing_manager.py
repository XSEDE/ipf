
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

import time

from ipf.document import Document
from teragrid.tgagent import TeraGridAgent
from teragrid.xmlhelper import *

##############################################################################################################

class ComputingManagerAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)
        self.description = "This agent provides documents in the GLUE 2 ComputingManager schema. For a batch scheduled system, this is typically that scheduler."
        self.default_timeout = 30

##############################################################################################################

class ComputingManager(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.ComputingManager"
        self.content_type = "text/xml"

        # Entity
        self.ID = None
        self.Name = None
        self.OtherInfo = [] # strings
        self.Extension = {} # (key,value) strings

        # Manager
        self.ProductName = None    # string
        self.ProductVersion = None # string

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
        self.ExecutionEnvironment = []          # list of string (uri)
        #self.executionEnvironments = None        # ExecutionEnvironments
        self.ApplicationEnvironment = []         # list of string (LocalID)
        self.Benchmark = []                      # list of string(LocalID)

        #self.computingShares = None              # ComputingShares

        # required attributes that may be forgotten
        self.ProductName = "unknown"

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

    def _setBody(self, body):
        logger.info("ComputingManager._setBody should parse the XML...")

    def _getBody(self):
        return self._toXml()

    def _toXml(self, indent=""):
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
