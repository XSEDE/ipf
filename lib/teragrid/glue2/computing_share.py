
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

import logging
import time

from ipf.document import Document
from teragrid.tgagent import TeraGridAgent
from teragrid.xmlhelper import *

logger = logging.getLogger("computing_share")

##############################################################################################################

# the queues to include are in ComputingShare

##############################################################################################################

class ComputingSharesAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)
        self.description = "This agent provides documents in the GLUE 2 ComputingShare schema. For a batch scheduled system, these are typically queues."
        self.default_timeout = 30

        #self.urlPath = "rdif/glue/ComputingShare/<Entities/ComputingShare/MappingQueue>"
        #self.shares = {}

    def _addActivities(self, activities, shares):
        shareDict = {}
        for share in shares:
            shareDict[share.Name] = share

        for share in shares:
            share.TotalJobs = 0
            share.RunningJobs = 0
            share.LocalRunningJobs = 0
            share.WaitingJobs = 0
            share.LocalWaitingJobs = 0
            share.SuspendedJobs = 0
            share.LocalSuspendedJobs = 0
            share.UsedSlots = 0
            share.RequestedSlots = 0
            share.computingActivity = []

        for activity in activities:
            #print(str(activity))
            share = shareDict.get(activity.Queue)
            if share == None:
                # output a warning
                print("  didn't find share for queue "+str(activity.Queue))
                continue

            share.computingActivity.append(activity)
            #activity.ComputingShare = [share.ID]
            if activity.State == "teragrid:running":
                share.RunningJobs = share.RunningJobs + 1
                share.LocalRunningJobs = share.LocalRunningJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.UsedSlots = share.UsedSlots + activity.RequestedSlots
            elif activity.State == "teragrid:pending":
                share.WaitingJobs = share.WaitingJobs + 1
                share.LocalWaitingJobs = share.LocalWaitingJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.RequestedSlots = share.RequestedSlots + activity.RequestedSlots
            elif activity.State == "teragrid:suspended":
                share.SuspendedJobs = share.SuspendedJobs + 1
                share.LocalSuspendedJobs = share.LocalSuspendedJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.RequestedSlots = share.RequestedSlots + activity.RequestedSlots
            elif activity.State == "teragrid:finished":
                pass
            elif activity.State == "teragrid:terminated":
                pass
            else:
                # output a warning
                pass

##############################################################################################################

class ComputingShare(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.ComputingShare"
        self.content_type = "text/xml"

        # Entity
        self.ID = None
        self.Name = None
        self.OtherInfo = [] # list of string
        self.Extension = {} # (key,value) strings

        # Share
        self.Description = None  # string
        self.Endpoint = []       # list of string (uri)
        self.Resource = []       # list of string (uri)
        self.Service = None      # string (uri)
        self.Activity = []       # list of string (uri)
        self.MappingPolicy = []  # list of string (uri)

        # ComputingShare
        self.MappingQueue = None                # string
        self.MaxWallTime =  None                # integer (s)
        self.MaxMultiSlotWallTime = None        # integer (s)
        self.MinWallTime = None                 # integer (s)
        self.DefaultWallTime = None             # integer (s)
        self.MaxCPUTime = None                  # integer (s)
        self.MaxTotalCPUTime = None             # integer (s)
        self.MinCPUTime = None                  # integer (s)
        self.DefaultCPUTime = None              # integer (s)
        self.MaxTotalJobs = None                # integer
        self.MaxRunningJobs = None              # integer
        self.MaxWaitingJobs = None              # integer
        self.MaxPreLRMSWaitingJobs = None       # integer
        self.MaxUserRunningJobs = None          # integer
        self.MaxSlotsPerJob = None              # integer
        self.MaxStageInStreams = None           # integer
        self.MaxStageOutStreams =  None         # integer
        self.SchedulingPolicy = None            # string?
        self.MaxMainMemory = None               # integer (MB)
        self.GuaranteedMainMemory =  None       # integer (MB)
        self.MaxVirtualMemory = None            # integer (MB)
        self.GuaranteedVirtualMemory = None     # integer (MB)
        self.MaxDiskSpace = None                # integer (GB)
        self.DefaultStorageService = None       # string - uri
        self.Preemption = None                  # boolean
        self.ServingState = None                # string
        self.TotalJobs = None                   # integer
        self.RunningJobs = None                 # integer
        self.LocalRunningJobs = None            # integer
        self.WaitingJobs = None                 # integer
        self.LocalWaitingJobs = None            # integer
        self.SuspendedJobs = None               # integer
        self.LocalSuspendedJobs = None          # integer
        self.StagingJobs = None                 # integer
        self.PreLRMSWaitingJobs = None          # integer
        self.EstimatedAverageWaitingTime = None # integer 
        self.EstimatedWorstWaitingTime = None   # integer
        self.FreeSlots = None                   # integer
        self.FreeSlotsWithDuration = None       # string 
        self.UsedSlots = None                   # integer
        self.RequestedSlots = None              # integer
        self.ReservationPolicy = None           # string
        self.Tag = []                           # list of string
        self.ComputingEndpoint = []             # list of string (uri)
        self.ExecutionEnvironment = []          # list of string (uri)
        self.ComputingService = None            # list of string (uri)
        self.ComputingActivity = []            # list of string (uri)
        #self.computingActivity = []             # list of ComputingActivity

        # LSF has Priority
        # LSF has MaxSlotsPerUser
        # LSF has access control
        # LSF has queue status

        # required attributes that may be forgotten
        self.ServingState = "production"


    def _setBody(self, body):
        logger.info("ComputingShare._setBody should parse the XML...")

    def _getBody(self):
        return self._toXml()

    def _toXml(self, indent=""):
        mstr = indent+"<ComputingShare"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name != None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"+key+"'>"+str(self.Extension[key])+"</Extension>\n"

        # Share
        if self.Description != None:
            mstr = mstr+indent+"  <Description>"+self.Description+"</Description>\n"
        for endpoint in self.Endpoint:
            mstr = mstr+indent+"  <Endpoint>"+endpoint+"</Endpoint>\n"
        for resource in self.Resource:
            mstr = mstr+indent+"  <Resource>"+resource+"</Resource>\n"
        if self.Service != None:
            mstr = mstr+indent+"  <Service>"+self.Service+"</Service>\n"
        for activity in self.Activity:
            mstr = mstr+indent+"  <Activity>"+activity+"</Activity>\n"
        for policy in self.MappingPolicy:
            mstr = mstr+indent+"  <MappingPolicy>"+policy+"</MappingPolicy>\n"

        # ComputingShare
        if self.MappingQueue != None:
            mstr = mstr+indent+"  <MappingQueue>"+self.MappingQueue+"</MappingQueue>\n"
        if self.MaxWallTime != None:
            mstr = mstr+indent+"  <MaxWallTime>"+str(self.MaxWallTime)+"</MaxWallTime>\n"
        if self.MaxMultiSlotWallTime != None:
            mstr = mstr+indent+"  <MaxTotalWallTime>"+str(self.MaxTotalWallTime)+"</MaxTotalWallTime>\n"
        if self.MinWallTime != None:
            mstr = mstr+indent+"  <MinWallTime>"+str(self.MinWallTime)+"</MinWallTime>\n"
        if self.DefaultWallTime != None:
            mstr = mstr+indent+"  <DefaultWallTime>"+str(self.DefaultWallTime)+"</DefaultWallTime>\n"
        if self.MaxCPUTime != None:
            mstr = mstr+indent+"  <MaxCPUTime>"+str(self.MaxCPUTime)+"</MaxCPUTime>\n"
        if self.MaxTotalCPUTime != None:
            mstr = mstr+indent+"  <MaxTotalCPUTime>"+str(self.MaxTotalCPUTime)+"</MaxTotalCPUTime>\n"
        if self.MinCPUTime != None:
            mstr = mstr+indent+"  <MinCPUTime>"+str(self.MinCPUTime)+"</MinCPUTime>\n"
        if self.DefaultCPUTime != None:
            mstr = mstr+indent+"  <DefaultCPUTime>"+str(self.DefaultCPUTime)+"</DefaultCPUTime>\n"
        if self.MaxTotalJobs != None:
            mstr = mstr+indent+"  <MaxTotalJobs>"+str(self.MaxTotalJobs)+"</MaxTotalJobs>\n"
        if self.MaxRunningJobs != None:
            mstr = mstr+indent+"  <MaxRunningJobs>"+str(self.MaxRunningJobs)+"</MaxRunningJobs>\n"
        if self.MaxWaitingJobs != None:
            mstr = mstr+indent+"  <MaxWaitingJobs>"+str(self.MaxWaitingJobs)+"</MaxWaitingJobs>\n"
        if self.MaxPreLRMSWaitingJobs != None:
            mstr = mstr+indent+"  <MaxPreLRMSWaitingJobs>"+str(self.MaxPreLRMSWaitingJobs)+ \
                   "</MaxPreLRMSWaitingJobs>\n"
        if self.MaxUserRunningJobs != None:
            mstr = mstr+indent+"  <MaxUserRunningJobs>"+str(self.MaxUserRunningJobs)+"</MaxUserRunningJobs>\n"
        if self.MaxSlotsPerJob != None:
            mstr = mstr+indent+"  <MaxSlotsPerJob>"+str(self.MaxSlotsPerJob)+"</MaxSlotsPerJob>\n"
        if self.MaxStageInStreams != None:
            mstr = mstr+indent+"  <MaxStageInStreams>"+str(self.MaxStageInStreams)+"</MaxStageInStreams>\n"
        if self.MaxStageOutStreams != None:
            mstr = mstr+indent+"  <MaxStageOutStreams>"+str(self.MaxStageOutStreams)+"</MaxStageOutStreams>\n"
        if self.SchedulingPolicy != None:
            mstr = mstr+indent+"  <SchedulingPolicy>"+self.SchedulingPolicy+"</SchedulingPolicy>\n"
        if self.MaxMainMemory != None:
            mstr = mstr+indent+"  <MaxMainMemory>"+str(self.MaxMainMemory)+"</MaxMainMemory>\n"
        if self.GuaranteedMainMemory != None:
            mstr = mstr+indent+"  <GuaranteedMainMemory>"+str(self.GuaranteedMainMemory)+"</GuaranteedMainMemory>\n"
        if self.MaxVirtualMemory != None:
            mstr = mstr+indent+"  <MaxVirtualMemory>"+str(self.MaxVirtualMemory)+"</MaxVirtualMemory>\n"
        if self.GuaranteedVirtualMemory != None:
            mstr = mstr+indent+"  <GuaranteedVirtualMemory>"+str(self.GuaranteedVirtualMemory)+ \
                   "</GuaranteedVirtualMemory>\n"
        if self.MaxDiskSpace != None:
            mstr = mstr+indent+"  <MaxDiskSpace>"+str(self.MaxDiskSpace)+"</MaxDiskSpace>\n"
        if self.DefaultStorageService != None:
            mstr = mstr+indent+"  <DefaultStorageService>"+self.DefaultStorageService+"</DefaultStorageService>\n"
        if self.Preemption != None:
            if self.Preemption:
                mstr = mstr+indent+"  <Preemption>true</Preemption>\n"
            else:
                mstr = mstr+indent+"  <Preemption>false</Preemption>\n"
        if self.ServingState != None:
            mstr = mstr+indent+"  <ServingState>"+self.ServingState+"</ServingState>\n"
        if self.TotalJobs != None:
            mstr = mstr+indent+"  <TotalJobs>"+str(self.TotalJobs)+"</TotalJobs>\n"
        if self.RunningJobs != None:
            mstr = mstr+indent+"  <RunningJobs>"+str(self.RunningJobs)+"</RunningJobs>\n"
        if self.LocalRunningJobs != None:
            mstr = mstr+indent+"  <LocalRunningJobs>"+str(self.LocalRunningJobs)+"</LocalRunningJobs>\n"
        if self.WaitingJobs != None:
            mstr = mstr+indent+"  <WaitingJobs>"+str(self.WaitingJobs)+"</WaitingJobs>\n"
        if self.LocalWaitingJobs != None:
            mstr = mstr+indent+"  <LocalWaitingJobs>"+str(self.LocalWaitingJobs)+"</LocalWaitingJobs>\n"
        if self.SuspendedJobs != None:
            mstr = mstr+indent+"  <SuspendedJobs>"+str(self.SuspendedJobs)+"</SuspendedJobs>\n"
        if self.LocalSuspendedJobs != None:
            mstr = mstr+indent+"  <LocalSuspendedJobs>"+str(self.LocalSuspendedJobs)+"</LocalSuspendedJobs>\n"
        if self.StagingJobs != None:
            mstr = mstr+indent+"  <StagingJobs>"+str(self.StagingJobs)+"</StagingJobs>\n"
        if self.PreLRMSWaitingJobs != None:
            mstr = mstr+indent+"  <PreLRMSWaitingJobs>"+str(self.PreLRMSWaitingJobs)+"</PreLRMSWaitingJobs>\n"
        if self.EstimatedAverageWaitingTime != None:
            mstr = mstr+indent+"  <EstimatedAverageWaitingTime>"+str(self.EstimatedAverageWaitingTime)+ \
                   "  </EstimatedAverageWaitingTime>\n"
        if self.EstimatedWorstWaitingTime != None:
            mstr = mstr+indent+"  <EstimatedWorstWaitingTime>"+str(self.EstimatedWorstWaitingTime)+ \
                   "  </EstimatedWorstWaitingTime>\n"
        if self.FreeSlots != None:
            mstr = mstr+indent+"  <FreeSlots>"+str(self.FreeSlots)+"</FreeSlots>\n"
        if self.FreeSlotsWithDuration != None:
            mstr = mstr+indent+"  <FreeSlotsWithDuration>"+str(self.FreeSlotsWithDuration)+ \
                   "</FreeSlotsWithDuration>\n"
        if self.UsedSlots != None:
            mstr = mstr+indent+"  <UsedSlots>"+str(self.UsedSlots)+"</UsedSlots>\n"
        if self.RequestedSlots != None:
            mstr = mstr+indent+"  <RequestedSlots>"+str(self.RequestedSlots)+"</RequestedSlots>\n"
        if self.ReservationPolicy != None:
            mstr = mstr+indent+"  <ReservationPolicy>"+str(self.ReservationPolicy)+"</ReservationPolicy>\n"
        for tag in self.Tag:
            mstr = mstr+indent+"  <Tag>"+tag+"</Tag>\n"
        for endpoint in self.ComputingEndpoint:
            mstr = mstr+indent+"  <ComputingEndpoint>"+endpoint+"</ComputingEndpoint>\n"
        for environment in self.ExecutionEnvironment:
            mstr = mstr+indent+"  <ExecutionEnvironment>"+environment+"</ExecutionEnvironment>\n"
        if self.ComputingService != None:
            mstr = mstr+indent+"  <ComputingService>"+str(self.ComputingService)+"</ComputingService>\n"
        # not outputting activity info for privacy/security
        #for activity in self.computingActivity:
        #    mstr = mstr+indent+"  <ComputingActivity>"+activity.ID+"</ComputingActivity>\n"
        mstr = mstr+indent+"</ComputingShare>\n"

        return mstr

