
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
from ipf.error import StepError
from ipf.sysinfo import ResourceName

from glue2.computing_activity import ComputingActivity, ComputingActivities
from glue2.step import GlueStep

#######################################################################################################################

class ComputingSharesStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "produces a document containing one or more GLUE 2 ComputingShare"
        self.time_out = 30
        self.requires = [ResourceName,ComputingActivities]
        self.produces = [ComputingShares]
        self._acceptParameter("queues",
                              "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. the expression is processed in order and the value for a queue at the end determines if it is shown.",
                              False)

        self.resource_name = None
        self.activities = None
        
    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.activities = self._getInput(ComputingActivities).activities

        shares = self._run()

        for share in shares:
            share.id = "%s.%s" % (share.MappingQueue,self.resource_name)
            share.ID = "urn:glue2:ComputingShare:%s.%s" % (share.MappingQueue,self.resource_name)
            share.ComputingService = "urn:glue2:ComputingService:%s" % (self.resource_name)

        self._addActivities(shares)

        self._output(ComputingShares(self.resource_name,shares))

    def _run(self):
        raise StepError("ComputingSharesStep._run not overriden")

    def _addActivities(self, shares):
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

        for activity in self.activities:
            if activity.Queue is None:
                self.debug("no queue specified for activity %s",activity)
                continue
            share = shareDict.get(activity.Queue)
            if share == None:
                self.warning("  didn't find share for queue "+str(activity.Queue))
                continue

            share.computingActivity.append(activity)
            if activity.State == ComputingActivity.STATE_RUNNING:
                share.RunningJobs = share.RunningJobs + 1
                share.LocalRunningJobs = share.LocalRunningJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.UsedSlots = share.UsedSlots + activity.RequestedSlots
            elif activity.State == ComputingActivity.STATE_PENDING:
                share.WaitingJobs = share.WaitingJobs + 1
                share.LocalWaitingJobs = share.LocalWaitingJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.RequestedSlots = share.RequestedSlots + activity.RequestedSlots
            elif activity.State == ComputingActivity.STATE_SUSPENDED:
                share.SuspendedJobs = share.SuspendedJobs + 1
                share.LocalSuspendedJobs = share.LocalSuspendedJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.RequestedSlots = share.RequestedSlots + activity.RequestedSlots
            elif activity.State == ComputingActivity.STATE_FINISHED:
                pass
            elif activity.State == ComputingActivity.STATE_TERMINATED:
                pass
            else:
                # output a warning
                pass

#######################################################################################################################

class ComputingShare(Data):
    def __init__(self):
        Data.__init__(self)
        
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = None
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
        self.ServingState = "production"        # string
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
        self.ComputingActivity = []             # list of string (uri)

        # LSF has Priority
        # LSF has MaxSlotsPerUser
        # LSF has access control
        # LSF has queue status

    def __str__(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

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

        # Share
        self.Description = doc.get("Description")
        self.Endpoint = doc.get("Endpoint",[])
        self.Resource = doc.get("Resource",[])
        self.Service = doc.get("Service")
        self.Activity = doc.get("Activity",[])
        self.MappingPolicy = doc.get("MappingPolicy",[])

        # ComputingShare
        self.MappingQueue = doc.get("MappingQueue")
        self.MaxWallTime = doc.get("MaxWallTime")
        self.MaxMultiSlotWallTime = doc.get("MaxMultiSlotWallTime")
        self.MinWallTime = doc.get("MinWallTime")
        self.DefaultWallTime = doc.get("DefaultWallTime")
        self.MaxCPUTime = doc.get("MaxCPUTime")
        self.MaxTotalCPUTime = doc.get("MaxTotalCPUTime")
        self.MinCPUTime = doc.get("MinCPUTime")
        self.DefaultCPUTime = doc.get("DefaultCPUTime")
        self.MaxTotalJobs = doc.get("MaxTotaoJobs")
        self.MaxRunningJobs = doc.get("MaxRunningJobs")
        self.MaxWaitingJobs = doc.get("MaxWaitingJobs")
        self.MaxPreLRMSWaitingJobs = doc.get("MaxPreLRMSWaitingJobs")
        self.MaxUserRunningJobs = doc.get("MaxUserRunningJobs")
        self.MaxSlotsPerJob = doc.get("MaxSlotsPerJob")
        self.MaxStageInStreams = doc.get("MaxStageInStreams")
        self.MaxStageOutStreams = doc.get("MaxStageOutStreams")
        self.SchedulingPolicy = doc.get("SchedulingPolicy")
        self.MaxMainMemory = doc.get("MaxMainMemory")
        self.GuaranteedMainMemory = doc.get("GuaranteedMainMemory")
        self.MaxVirtualMemory = doc.get("MaxVirtualMemory")
        self.GuaranteedVirtualMemory = doc.get("GuaranteedVirtualMemory")
        self.MaxDiskSpace = doc.get("MaxDiskSpace")
        self.DefaultStorageService = doc.get("DefaultStorageService")
        self.Preemption = doc.get("Preemption")
        self.ServingState = doc.get("ServingState")
        self.TotalJobs = doc.get("TotalJobs")
        self.RunningJobs = doc.get("RunningJobs")
        self.LocalRunningJobs = doc.get("LocalRunningJobs")
        self.WaitingJobs = doc.get("WaitingJobs")
        self.LocalWaitingJobs = doc.get("LocalWaitingJobs")
        self.SuspendedJobs = doc.get("SuspendedJobs")
        self.LocalSuspendedJobs = doc.get("LocalSuspendedJobs")
        self.StagingJobs = doc.get("StagingJobs")
        self.PreLRMSWaitingJobs = doc.get("PreLRMSWaitingJobs")
        self.EstimatedAverageWaitingTime = doc.get("EstimatedAverageWaitingTime")
        self.EstimatedWorstWaitingTime = doc.get("EstimatedWorstWaitingTime")
        self.FreeSlots = doc.get("FreeSlots")
        self.FreeSlotsWithDuration = doc.get("FreeSlotsWithDuration")
        self.UsedSlots = doc.get("UsedSlots")
        self.RequestedSlots = doc.get("RequestedSlots")
        self.ReservationPolicy = doc.get("ReservationPolicy")
        self.Tag = doc.get("Tag",[])
        self.ComputingEndpoint = doc.get("ComputingEndpoint",[])
        self.ComputingService = doc.get("ComputingService")

#######################################################################################################################

class ComputingShareTeraGridXml(Representation):
    data_cls = ComputingShare

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(share):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingShare")
        doc.documentElement.appendChild(root)

        # Entity
        root.setAttribute("CreationTime",dateTimeToText(share.CreationTime))
        if share.Validity is not None:
            root.setAttribute("Validity",str(share.Validity))

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(share.ID))
        root.appendChild(e)

        if share.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(share.Name))
            root.appendChild(e)
        for info in share.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        for key in share.Extension:
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(str(share.Extension[key])))
            root.appendChild(e)

        # Share
        if share.Description is not None:
            e = doc.createElement("Description")
            e.appendChild(doc.createTextNode(share.Description))
            root.appendChild(e)
        for endpoint in share.Endpoint:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for resource in share.Resource:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(resource))
            root.appendChild(e)
        if share.Service is not None:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(share.Service))
            root.appendChild(e)
        for activity in share.Activity:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(activity))
            root.appendChild(e)
        for policy in share.MappingPolicy:
            e = doc.createElement("MappingPolicy")
            e.appendChild(doc.createTextNode(policy))
            root.appendChild(e)

        # ComputingShare
        if share.MappingQueue is not None:
            e = doc.createElement("MappingQueue")
            e.appendChild(doc.createTextNode(share.MappingQueue))
            root.appendChild(e)
        if share.MaxWallTime is not None:
            e = doc.createElement("MaxWallTime")
            e.appendChild(doc.createTextNode(str(share.MaxWallTime)))
            root.appendChild(e)
        if share.MaxMultiSlotWallTime is not None:
            e = doc.createElement("MaxMultiSlotWallTime")
            e.appendChild(doc.createTextNode(str(share.MaxMultiSlotWallTime)))
            root.appendChild(e)
        if share.MinWallTime is not None:
            e = doc.createElement("MinWallTime")
            e.appendChild(doc.createTextNode(str(share.MinWallTime)))
            root.appendChild(e)
        if share.DefaultWallTime is not None:
            e = doc.createElement("DefaultWallTime")
            e.appendChild(doc.createTextNode(str(share.DefaultWallTime)))
            root.appendChild(e)
        if share.MaxCPUTime is not None:
            e = doc.createElement("MaxCPUTime")
            e.appendChild(doc.createTextNode(str(share.MaxCPUTime)))
            root.appendChild(e)
        if share.MaxTotalCPUTime is not None:
            e = doc.createElement("MaxTotalCPUTime")
            e.appendChild(doc.createTextNode(str(share.MaxTotalCPUTime)))
            root.appendChild(e)
        if share.MinCPUTime is not None:
            e = doc.createElement("MinCPUTime")
            e.appendChild(doc.createTextNode(str(share.MinCPUTime)))
            root.appendChild(e)
        if share.DefaultCPUTime is not None:
            e = doc.createElement("DefaultCPUTime")
            e.appendChild(doc.createTextNode(str(share.DefaultCPUTime)))
            root.appendChild(e)
        if share.MaxTotalJobs is not None:
            e = doc.createElement("MaxTotalJobs")
            e.appendChild(doc.createTextNode(str(share.MaxTotalJobs)))
            root.appendChild(e)
        if share.MaxRunningJobs is not None:
            e = doc.createElement("MaxRunningJobs")
            e.appendChild(doc.createTextNode(str(share.MaxRunningJobs)))
            root.appendChild(e)
        if share.MaxWaitingJobs is not None:
            e = doc.createElement("MaxWaitingJobs")
            e.appendChild(doc.createTextNode(str(share.MaxWaitingJobs)))
            root.appendChild(e)
        if share.MaxPreLRMSWaitingJobs is not None:
            e = doc.createElement("MaxPreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(share.MaxPreLRMSWaitingJobs)))
            root.appendChild(e)
        if share.MaxUserRunningJobs is not None:
            e = doc.createElement("MaxUserRunningJobs")
            e.appendChild(doc.createTextNode(str(share.MaxUserRunningJobs)))
            root.appendChild(e)
        if share.MaxSlotsPerJob is not None:
            e = doc.createElement("MaxSlotsPerJob")
            e.appendChild(doc.createTextNode(str(share.MaxSlotsPerJob)))
            root.appendChild(e)
        if share.MaxStageInStreams is not None:
            e = doc.createElement("MaxStageInStreams")
            e.appendChild(doc.createTextNode(str(share.MaxStageInStreams)))
            root.appendChild(e)
        if share.MaxStageOutStreams is not None:
            e = doc.createElement("MaxStageOutStreams")
            e.appendChild(doc.createTextNode(str(share.MaxStageOutStreams)))
            root.appendChild(e)
        if share.SchedulingPolicy is not None:
            e = doc.createElement("SchedulingPolicy")
            e.appendChild(doc.createTextNode(share.SchedulingPolicy))
            root.appendChild(e)
        if share.MaxMainMemory is not None:
            e = doc.createElement("MaxMainMemory")
            e.appendChild(doc.createTextNode(str(share.MaxMainMemory)))
            root.appendChild(e)
        if share.GuaranteedMainMemory is not None:
            e = doc.createElement("GuaranteedMainMemory")
            e.appendChild(doc.createTextNode(str(share.GuaranteedMainMemory)))
            root.appendChild(e)
        if share.MaxVirtualMemory is not None:
            e = doc.createElement("MaxVirtualMemory")
            e.appendChild(doc.createTextNode(str(share.MaxVirtualMemory)))
            root.appendChild(e)
        if share.GuaranteedVirtualMemory is not None:
            e = doc.createElement("GuaranteedVirtualMemory")
            e.appendChild(doc.createTextNode(str(share.GuaranteedVirtualMemory)))
            root.appendChild(e)
        if share.MaxDiskSpace is not None:
            e = doc.createElement("MaxDiskSpace")
            e.appendChild(doc.createTextNode(str(share.MaxDiskSpace)))
            root.appendChild(e)
        if share.DefaultStorageService is not None:
            e = doc.createElement("DefaultStorageService")
            e.appendChild(doc.createTextNode(share.DefaultStorageService))
            root.appendChild(e)
        if share.Preemption is not None:
            e = doc.createElement("Preemption")
            if share.Preemption:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if share.ServingState is not None:
            e = doc.createElement("ServingState")
            e.appendChild(doc.createTextNode(share.ServingState))
            root.appendChild(e)
        if share.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(share.TotalJobs)))
            root.appendChild(e)
        if share.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(share.RunningJobs)))
            root.appendChild(e)
        if share.LocalRunningJobs is not None:
            e = doc.createElement("LocalRunningJobs")
            e.appendChild(doc.createTextNode(str(share.LocalRunningJobs)))
            root.appendChild(e)
        if share.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(share.WaitingJobs)))
            root.appendChild(e)
        if share.LocalWaitingJobs is not None:
            e = doc.createElement("LocalWaitingJobs")
            e.appendChild(doc.createTextNode(str(share.LocalWaitingJobs)))
            root.appendChild(e)
        if share.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(share.SuspendedJobs)))
            root.appendChild(e)
        if share.LocalSuspendedJobs is not None:
            e = doc.createElement("LocalSuspendedJobs")
            e.appendChild(doc.createTextNode(str(share.LocalSuspendedJobs)))
            root.appendChild(e)
        if share.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(share.StagingJobs)))
            root.appendChild(e)
        if share.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(share.PreLRMSWaitingJobs)))
            root.appendChild(e)
        if share.EstimatedAverageWaitingTime is not None:
            e = doc.createElement("EstimatedAverageWaitingTime")
            e.appendChild(doc.createTextNode(str(share.EstimatedAverageWaitingTime)))
            root.appendChild(e)
        if share.EstimatedWorstWaitingTime is not None:
            e = doc.createElement("EstimatedWorstWaitingTime")
            e.appendChild(doc.createTextNode(str(share.EstimatedWorstWaitingTime)))
            root.appendChild(e)
        if share.FreeSlots is not None:
            e = doc.createElement("FreeSlots")
            e.appendChild(doc.createTextNode(str(share.FreeSlots)))
            root.appendChild(e)
        if share.FreeSlotsWithDuration is not None:
            e = doc.createElement("FreeSlotsWithDuration")
            e.appendChild(doc.createTextNode(share.FreeSlotsWithDuration))
            root.appendChild(e)
        if share.UsedSlots is not None:
            e = doc.createElement("UsedSlots")
            e.appendChild(doc.createTextNode(str(share.UsedSlots)))
            root.appendChild(e)
        if share.RequestedSlots is not None:
            e = doc.createElement("RequestedSlots")
            e.appendChild(doc.createTextNode(str(share.RequestedSlots)))
            root.appendChild(e)
        if share.ReservationPolicy is not None:
            e = doc.createElement("ReservationPolicy")
            e.appendChild(doc.createTextNode(share.Service))
            root.appendChild(e)
        for tag in share.Tag:
            e = doc.createElement("Tag")
            e.appendChild(doc.createTextNode(tag))
            root.appendChild(e)
        for endpoint in share.ComputingEndpoint:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for environment in share.ExecutionEnvironment:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(environment))
            root.appendChild(e)
        if share.ComputingService is not None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(share.ComputingService))
            root.appendChild(e)

        return doc

#######################################################################################################################

class ComputingShareIpfJson(Representation):
    data_cls = ComputingShare

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(share):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(share.CreationTime)
        if share.Validity is not None:
            doc["Validity"] = share.Validity
        doc["ID"] = share.ID
        if share.Name is not None:
            doc["Name"] = share.Name
        if len(share.OtherInfo) > 0:
            doc["OtherInfo"] = share.OtherInfo
        if len(share.Extension) > 0:
            doc["Extension"] = share.Extension

        # Share
        if share.Description is not None:
            doc["Description"] = share.Description
        if len(share.Endpoint) > 0:
            doc["Endpoint"] = share.Endpoint
        if len(share.Resource) > 0:
            doc["Resource"] = share.Resource
        if share.Service is not None:
            doc["Service"] = share.Service
        if len(share.Activity) > 0:
            doc["Activity"] = share.Activity
        if len(share.MappingPolicy) > 0:
            doc["MappingPolicy"] = share.MappingPolicy

        # ComputingShare
        if share.MappingQueue is not None:
            doc["MappingQueue"] = share.MappingQueue
        if share.MaxWallTime is not None:
            doc["MaxWallTime"] = share.MaxWallTime
        if share.MaxMultiSlotWallTime is not None:
            doc["MaxMultiSlotWallTime"] = share.MaxMultiSlotWallTime
        if share.MinWallTime is not None:
            doc["MinWallTime"] = share.MinWallTime
        if share.DefaultWallTime is not None:
            doc["DefaultWallTime"] = share.DefaultWallTime
        if share.MaxCPUTime is not None:
            doc["MaxCPUTime"] = share.MaxCPUTime
        if share.MaxTotalCPUTime is not None:
            doc["MaxTotalCPUTime"] = share.MaxTotalCPUTime
        if share.MinCPUTime is not None:
            doc["MinCPUTime"] = share.MinCPUTime
        if share.DefaultCPUTime is not None:
            doc["DefaultCPUTime"] = share.DefaultCPUTime
        if share.MaxTotalJobs is not None:
            doc["MaxTotalJobs"] = share.MaxTotalJobs
        if share.MaxRunningJobs is not None:
            doc["MaxRunningJobs"] = share.MaxRunningJobs
        if share.MaxWaitingJobs is not None:
            doc["MaxWaitingJobs"] = share.MaxWaitingJobs
        if share.MaxPreLRMSWaitingJobs is not None:
            doc["MaxPreLRMSWaitingJobs"] = share.MaxPreLRMSWaitingJobs
        if share.MaxUserRunningJobs is not None:
            doc["MaxUserRunningJobs"] = share.MaxUserRunningJobs
        if share.MaxSlotsPerJob is not None:
            doc["MaxSlotsPerJob"] = share.MaxSlotsPerJob
        if share.MaxStageInStreams is not None:
            doc["MaxStageInStreams"] = share.MaxStageInStreams
        if share.MaxStageOutStreams is not None:
            doc["MaxStageOutStreams"] = share.MaxStageOutStreams
        if share.SchedulingPolicy is not None:
            doc["SchedulingPolicy"] = share.SchedulingPolicy
        if share.MaxMainMemory is not None:
            doc["MaxMainMemory"] = share.MaxMainMemory
        if share.GuaranteedMainMemory is not None:
            doc["GuaranteedMainMemory"] = share.GuaranteedMainMemory
        if share.MaxVirtualMemory is not None:
            doc["MaxVirtualMemory"] = share.MaxVirtualMemory
        if share.GuaranteedVirtualMemory is not None:
            doc["GuaranteedVirtualMemory"] = share.GuaranteedVirtualMemory
        if share.MaxDiskSpace is not None:
            doc["MaxDiskSpace"] = share.MaxDiskSpace
        if share.DefaultStorageService is not None:
            doc["DefaultStorageService"] = share.DefaultStorageService
        if share.Preemption is not None:
            doc["Preemption"] = share.Preemption
        if share.ServingState is not None:
            doc["ServingState"] = share.ServingState
        if share.TotalJobs is not None:
            doc["TotalJobs"] = share.TotalJobs
        if share.RunningJobs is not None:
            doc["RunningJobs"] = share.RunningJobs
        if share.LocalRunningJobs is not None:
            doc["LocalRunningJobs"] = share.LocalRunningJobs
        if share.WaitingJobs is not None:
            doc["WaitingJobs"] = share.WaitingJobs
        if share.LocalWaitingJobs is not None:
            doc["LocalWaitingJobs"] = share.LocalWaitingJobs
        if share.SuspendedJobs is not None:
            doc["SuspendedJobs"] = share.SuspendedJobs
        if share.LocalSuspendedJobs is not None:
            doc["LocalSuspendedJobs"] = share.LocalSuspendedJobs
        if share.StagingJobs is not None:
            doc["StagingJobs"] = share.StagingJobs
        if share.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = share.PreLRMSWaitingJobs
        if share.EstimatedAverageWaitingTime is not None:
            doc["EstimatedAverageWaitingTime"] = share.EstimatedAverageWaitingTime
        if share.EstimatedWorstWaitingTime is not None:
            doc["EstimatedWorstWaitingTime"] = share.EstimatedWorstWaitingTime
        if share.FreeSlots is not None:
            doc["FreeSlots"] = share.FreeSlots
        if share.FreeSlotsWithDuration is not None:
            doc["FreeSlotsWithDuration"] = share.FreeSlotsWithDuration
        if share.UsedSlots is not None:
            doc["UsedSlots"] = share.UsedSlots
        if share.RequestedSlots is not None:
            doc["RequestedSlots"] = share.RequestedSlots
        if share.ReservationPolicy is not None:
            doc["ReservationPolicy"] = share.ReservationPolicy
        if len(share.Tag) > 0:
            doc["Tag"] = share.Tag
        if len(share.ComputingEndpoint):
            doc["ComputingEndpoint"] = share.ComputingEndpoint
        if len(share.ExecutionEnvironment):
            doc["ExecutionEnvironment"] = share.ExecutionEnvironment
        if share.ComputingService is not None:
            doc["ComputingService"] = share.ComputingService

        return doc

#######################################################################################################################

class ComputingShares(Data):
    def __init__(self, id, shares):
        Data.__init__(self,id)
        self.shares = shares

#######################################################################################################################

class ComputingSharesTeraGridXml(Representation):
    data_cls = ComputingShares

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data.shares).toprettyxml()

    @staticmethod
    def toDom(shares):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for share in shares:
            sdoc = ComputingShareTeraGridXml.toDom(share)
            doc.documentElement.appendChild(sdoc.documentElement.firstChild)
        return doc

#######################################################################################################################

class ComputingSharesIpfJson(Representation):
    data_cls = ComputingShares

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data.shares),sort_keys=True,indent=4)

    @staticmethod
    def toJson(shares):
        sdoc = []
        for share in shares:
            sdoc.append(ComputingShareIpfJson.toJson(share))
        return sdoc

#######################################################################################################################
