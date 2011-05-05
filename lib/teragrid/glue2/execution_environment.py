
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
import os
import socket
import sys
import time

import ConfigParser

from ipf.document import Document
from teragrid.tgagent import TeraGridAgent
from teragrid.xmlhelper import *
from teragrid.glue2.computing_activity import includeQueue

##############################################################################################################

class ExecutionEnvironmentsAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)
        self.description = "This agent provides documents in the GLUE 2 ExecutionEnvironment schema. For a batch scheduled system, these are typically nodes."
        self.defaultTimeOut = 60
        self._setTeraGridPlatform()
        
    def _setTeraGridPlatform(self):
        if ExecutionEnvironment.teragrid_platform != None:
            return

        try:
            ExecutionEnvironment.teragrid_platform = self.config.get("teragrid","whatami")
            return
        except ConfigParser.Error:
            pass
        tg_whatami = "tgwhatami"
        try:
            tg_whatami = self.config.get("teragrid","tgwhatami")
        except ConfigParser.Error:
            pass
        (status, output) = commands.getstatusoutput(tg_whatami)
        if status == 0:
            ExecutionEnvironment.teragrid_platform = output

    def _goodHost(self, host):
        # check that it has cpu information
        if host.PhysicalCPUs == None:
            return False

        # check that it is associated with a good queue
        for queue in host.ComputingShare:
            if includeQueue(self.config,queue):
                return True
        return False

##############################################################################################################

class ExecutionEnvironment(Document):
    teragrid_platform = None

    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.ExecutionEnvironment"
        self.content_type = "text/xml"

        # Entity
        self.ID = None
        self.Name = None
        self.OtherInfo = [] # strings
        self.Extension = {} # (key,value) strings

        # Resource
        self.Manager = None # string (uri)
        self.Share = []     # list of string (uri)
        self.Activity = []  # list of string (uri)

        # ExecutionEnvironment
        self.Platform = None              # string (Platform_t)
        self.VirtualMachine = None        # boolean (ExtendedBoolean)
        self.TotalInstances = None        # integer
        self.UsedInstances = None         # integer
        self.UnavailableInstances = None  # integer
        self.PhysicalCPUs = None          # integer
        self.LogicalCPUs = None           # integer
        self.CPUMultiplicity = None       # integer (CPUMultiplicity)
        self.CPUVendor = None             # string
        self.CPUModel = None              # string
        self.CPUVersion = None            # string
        self.CPUClockSpeed = None         # integer (MHz)
        self.CPUTimeScalingFactor = None  # float
        self.WallTimeScalingFactor = None # float
        self.MainMemorySize = None        # integer (MB)
        self.VirtualMemorySize = None     # integer (MB)
        self.OSFamily = None              # string (OSFamily)
        self.OSName = None                # string (OSName)
        self.OSVersion = None             # string
        self.ConnectivityIn = None        # boolean (ExtendedBoolean)
        self.ConnectivityOut = None       # boolean (ExtendedBoolean)
        self.NetworkInfo = None           # string (NetworkInfo)
        self.ComputingManager = None      # string (uri)
        self.ComputingShare = []          # list of string (LocalID)
        self.ComputingActivity = []       # list of string (uri)
        self.ApplicationEnvironment = []  # list of string (LocalID)
        self.Benchmark = []               # list of string (LocalID)

        # set defaults to be the same as the host where this runs
        (sysName,nodeName,release,version,machine) = os.uname()
        self.Platform = machine
        self.OSFamily = sysName.lower()
        self.OSName = sysName.lower()
        self.OSVersion = release

        if self.teragrid_platform != None:
            self.Extension["TeraGridPlatform"] = self.teragrid_platform

        # required attributes that may be forgotten
        self.MainMemorySize = 0

    def _setBody(self, body):
        logger.info("ExecutionEnvironment._setBody should parse the XML...")

    def _getBody(self):
        return self._toXml()

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
    
    def _toXml(self, indent=""):
        mstr = indent+"<ExecutionEnvironment"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                      Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+str(self.ID)+"</ID>\n"
        if self.Name != None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"+key+"'>"+self.Extension[key]+"</Extension>\n"

        # Resource
        if self.Manager != None:
            mstr = mstr+indent+"  <Manager>"+self.Manager+"</Manager>\n"
        for share in self.Share:
            mstr = mstr+indent+"  <Share>"+share+"</Share>\n"
        for activity in self.Activity:
            mstr = mstr+indent+"  <Activity>"+activity+"</Activity>\n"

        # ExecutionEnvironment
        if self.Platform != None:
            mstr = mstr+indent+"  <Platform>"+self.Platform+"</Platform>\n"
        if self.VirtualMachine != None:
            if self.VirtualMachine:
                mstr = mstr+indent+"  <VirtualMachine>true</VirtualMachine>\n"
            else:
                mstr = mstr+indent+"  <VirtualMachine>false</VirtualMachine>\n"
        if self.TotalInstances != None:
            mstr = mstr+indent+"  <TotalInstances>"+str(self.TotalInstances)+"</TotalInstances>\n"
        if self.UsedInstances != None:
            mstr = mstr+indent+"  <UsedInstances>"+str(self.UsedInstances)+"</UsedInstances>\n"
        if self.UnavailableInstances != None:
            mstr = mstr+indent+"  <UnavailableInstances>"+str(self.UnavailableInstances)+"</UnavailableInstances>\n"
        if self.PhysicalCPUs != None:
            mstr = mstr+indent+"  <PhysicalCPUs>"+str(self.PhysicalCPUs)+"</PhysicalCPUs>\n"
        if self.LogicalCPUs != None:
            mstr = mstr+indent+"  <LogicalCPUs>"+str(self.LogicalCPUs)+"</LogicalCPUs>\n"
        if self.CPUMultiplicity != None:
            mstr = mstr+indent+"  <CPUMultiplicity>"+self.CPUMultiplicity+"</CPUMultiplicity>\n"
        if self.CPUVendor != None:
            mstr = mstr+indent+"  <CPUVendor>"+self.CPUVendor+"</CPUVendor>\n"
        if self.CPUModel != None:
            mstr = mstr+indent+"  <CPUModel>"+self.CPUModel+"</CPUModel>\n"
        if self.CPUVersion != None:
            mstr = mstr+indent+"  <CPUVersion>"+self.CPUVersion+"</CPUVersion>\n"
        if self.CPUClockSpeed != None:
            mstr = mstr+indent+"  <CPUClockSpeed>"+str(self.CPUClockSpeed)+"</CPUClockSpeed>\n"
        if self.CPUTimeScalingFactor != None:
            mstr = mstr+indent+"  <CPUTimeScalingFactor>"+str(self.CPUTimeScalingFactor)+"</CPUTimeScalingFactor>\n"
        if self.WallTimeScalingFactor != None:
            mstr = mstr+indent+"  <WallTimeScalingFactor>"+str(self.WallTimeScalingFactor)+"</WallTimeScalingFactor>\n"
        if self.MainMemorySize != None:
            mstr = mstr+indent+"  <MainMemorySize>"+str(self.MainMemorySize)+"</MainMemorySize>\n"
        if self.VirtualMemorySize != None:
            mstr = mstr+indent+"  <VirtualMemorySize>"+str(self.VirtualMemorySize)+"</VirtualMemorySize>\n"
        if self.OSFamily != None:
            mstr = mstr+indent+"  <OSFamily>"+self.OSFamily+"</OSFamily>\n"
        if self.OSName != None:
            mstr = mstr+indent+"  <OSName>"+self.OSName+"</OSName>\n"
        if self.OSVersion != None:
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
        if self.NetworkInfo != None:
            mstr = mstr+indent+"  <NetworkInfo>"+self.NetworkInfo+"</NetworkInfo>\n"
        if self.ComputingManager != None:
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
