
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
from ipf.error import StepError
from ipf.sysinfo import ResourceName

from .computing_activity import ComputingActivity, ComputingActivities
from .accelerator_environment import AcceleratorEnvironments
#from .computing_share_accel_info import ComputingShareAcceleratorInfo
from .step import GlueStep
from .share import *

#######################################################################################################################

class ComputingSharesStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "produces a document containing one or more GLUE 2 ComputingShare"
        #self.time_out = 30
        self.time_out = 120
        #self.requires = [ResourceName,ComputingActivities,ComputingShareAcceleratorInfo]
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
            share.id = "%s.%s" % (share.Name,self.resource_name)
            share.ID = "urn:glue2:ComputingShare:%s.%s" % (share.Name,self.resource_name)
            share.ServiceID = "urn:glue2:ComputingService:%s" % (self.resource_name)

        self._addActivities(shares)
        for share in shares:
            if share.UsedAcceleratorSlots > 0:
                share.ComputingShareAccelInfoID = "urn:glue2:ComputingShareAcceleratorInfo:%s.%s" % (share.Name,self.resource_name)

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
            share.WaitingJobs = 0
            share.SuspendedJobs = 0
            share.UsedSlots = 0
            share.UsedAcceleratorSlots = 0
            share.RequestedSlots = 0
            share.activity = []

        for activity in self.activities:
            if activity.Queue is None:
                self.debug("no queue specified for activity %s",activity)
                continue
            try:
                # if an activity is associated with a reservation, use that share
                share = shareDict[activity.Extension["ReservationName"]]
            except KeyError:
                try:
                    share = shareDict[activity.Queue]
                except KeyError:
                    self.warning("  didn't find share for queue "+str(activity.Queue))
                    continue
            share.activity.append(activity)
            if activity.State[0] == ComputingActivity.STATE_RUNNING:
                share.RunningJobs = share.RunningJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.UsedSlots = share.UsedSlots + activity.RequestedSlots
                share.UsedAcceleratorSlots = share.UsedAcceleratorSlots + activity.RequestedAcceleratorSlots
            elif activity.State[0] == ComputingActivity.STATE_PENDING:
                share.WaitingJobs = share.WaitingJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.RequestedSlots = share.RequestedSlots + activity.RequestedSlots
            elif activity.State[0] == ComputingActivity.STATE_SUSPENDED:
                share.SuspendedJobs = share.SuspendedJobs + 1
                share.TotalJobs = share.TotalJobs + 1
                share.RequestedSlots = share.RequestedSlots + activity.RequestedSlots
            elif activity.State[0] == ComputingActivity.STATE_FINISHED:
                pass
            elif activity.State[0] == ComputingActivity.STATE_TERMINATED:
                pass
            else:
                # output a warning
                pass

#######################################################################################################################

class ComputingShare(Share):
    def __init__(self):
        Share.__init__(self)

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
        self.UsedAcceleratorSlots = None        # integer
        self.RequestedSlots = None              # integer
        self.ReservationPolicy = None           # string
        self.ComputingShareAccelInfoID = ""     # string
        self.Tag = []                           # list of string
        # use Endpoint, Resource, Service, Activity from Share
        #   instead of ComputingEndpoint, ExecutionEnvironment, ComputingService, ComputingActivity

        # LSF has Priority
        # LSF has MaxSlotsPerUser
        # LSF has access control
        # LSF has queue status

#######################################################################################################################

class ComputingShareTeraGridXml(ShareTeraGridXml):
    data_cls = ComputingShare

    def __init__(self, data):
        ShareTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingShare")
        doc.documentElement.appendChild(root)

        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        ShareTeraGridXml.addToDomElement(self,doc,element)

        if self.data.MappingQueue is not None:
            e = doc.createElement("MappingQueue")
            e.appendChild(doc.createTextNode(self.data.MappingQueue))
            element.appendChild(e)
        if self.data.MaxWallTime is not None:
            e = doc.createElement("MaxWallTime")
            e.appendChild(doc.createTextNode(str(self.data.MaxWallTime)))
            element.appendChild(e)
        if self.data.MaxMultiSlotWallTime is not None:
            e = doc.createElement("MaxMultiSlotWallTime")
            e.appendChild(doc.createTextNode(str(self.data.MaxMultiSlotWallTime)))
            element.appendChild(e)
        if self.data.MinWallTime is not None:
            e = doc.createElement("MinWallTime")
            e.appendChild(doc.createTextNode(str(self.data.MinWallTime)))
            element.appendChild(e)
        if self.data.DefaultWallTime is not None:
            e = doc.createElement("DefaultWallTime")
            e.appendChild(doc.createTextNode(str(self.data.DefaultWallTime)))
            element.appendChild(e)
        if self.data.MaxCPUTime is not None:
            e = doc.createElement("MaxCPUTime")
            e.appendChild(doc.createTextNode(str(self.data.MaxCPUTime)))
            element.appendChild(e)
        if self.data.MaxTotalCPUTime is not None:
            e = doc.createElement("MaxTotalCPUTime")
            e.appendChild(doc.createTextNode(str(self.data.MaxTotalCPUTime)))
            element.appendChild(e)
        if self.data.MinCPUTime is not None:
            e = doc.createElement("MinCPUTime")
            e.appendChild(doc.createTextNode(str(self.data.MinCPUTime)))
            element.appendChild(e)
        if self.data.DefaultCPUTime is not None:
            e = doc.createElement("DefaultCPUTime")
            e.appendChild(doc.createTextNode(str(self.data.DefaultCPUTime)))
            element.appendChild(e)
        if self.data.MaxTotalJobs is not None:
            e = doc.createElement("MaxTotalJobs")
            e.appendChild(doc.createTextNode(str(self.data.MaxTotalJobs)))
            element.appendChild(e)
        if self.data.MaxRunningJobs is not None:
            e = doc.createElement("MaxRunningJobs")
            e.appendChild(doc.createTextNode(str(self.data.MaxRunningJobs)))
            element.appendChild(e)
        if self.data.MaxWaitingJobs is not None:
            e = doc.createElement("MaxWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.MaxWaitingJobs)))
            element.appendChild(e)
        if self.data.MaxPreLRMSWaitingJobs is not None:
            e = doc.createElement("MaxPreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.MaxPreLRMSWaitingJobs)))
            element.appendChild(e)
        if self.data.MaxUserRunningJobs is not None:
            e = doc.createElement("MaxUserRunningJobs")
            e.appendChild(doc.createTextNode(str(self.data.MaxUserRunningJobs)))
            element.appendChild(e)
        if self.data.MaxSlotsPerJob is not None:
            e = doc.createElement("MaxSlotsPerJob")
            e.appendChild(doc.createTextNode(str(self.data.MaxSlotsPerJob)))
            element.appendChild(e)
        if self.data.MaxStageInStreams is not None:
            e = doc.createElement("MaxStageInStreams")
            e.appendChild(doc.createTextNode(str(self.data.MaxStageInStreams)))
            element.appendChild(e)
        if self.data.MaxStageOutStreams is not None:
            e = doc.createElement("MaxStageOutStreams")
            e.appendChild(doc.createTextNode(str(self.data.MaxStageOutStreams)))
            element.appendChild(e)
        if self.data.SchedulingPolicy is not None:
            e = doc.createElement("SchedulingPolicy")
            e.appendChild(doc.createTextNode(self.data.SchedulingPolicy))
            element.appendChild(e)
        if self.data.MaxMainMemory is not None:
            e = doc.createElement("MaxMainMemory")
            e.appendChild(doc.createTextNode(str(self.data.MaxMainMemory)))
            element.appendChild(e)
        if self.data.GuaranteedMainMemory is not None:
            e = doc.createElement("GuaranteedMainMemory")
            e.appendChild(doc.createTextNode(str(self.data.GuaranteedMainMemory)))
            element.appendChild(e)
        if self.data.MaxVirtualMemory is not None:
            e = doc.createElement("MaxVirtualMemory")
            e.appendChild(doc.createTextNode(str(self.data.MaxVirtualMemory)))
            element.appendChild(e)
        if self.data.GuaranteedVirtualMemory is not None:
            e = doc.createElement("GuaranteedVirtualMemory")
            e.appendChild(doc.createTextNode(str(self.data.GuaranteedVirtualMemory)))
            element.appendChild(e)
        if self.data.MaxDiskSpace is not None:
            e = doc.createElement("MaxDiskSpace")
            e.appendChild(doc.createTextNode(str(self.data.MaxDiskSpace)))
            element.appendChild(e)
        if self.data.DefaultStorageService is not None:
            e = doc.createElement("DefaultStorageService")
            e.appendChild(doc.createTextNode(self.data.DefaultStorageService))
            element.appendChild(e)
        if self.data.Preemption is not None:
            e = doc.createElement("Preemption")
            if self.data.Preemption:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            element.appendChild(e)
        if self.data.ServingState is not None:
            e = doc.createElement("ServingState")
            e.appendChild(doc.createTextNode(self.data.ServingState))
            element.appendChild(e)
        if self.data.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(self.data.TotalJobs)))
            element.appendChild(e)
        if self.data.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(self.data.RunningJobs)))
            element.appendChild(e)
        if self.data.LocalRunningJobs is not None:
            e = doc.createElement("LocalRunningJobs")
            e.appendChild(doc.createTextNode(str(self.data.LocalRunningJobs)))
            element.appendChild(e)
        if self.data.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.WaitingJobs)))
            element.appendChild(e)
        if self.data.LocalWaitingJobs is not None:
            e = doc.createElement("LocalWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.LocalWaitingJobs)))
            element.appendChild(e)
        if self.data.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(self.data.SuspendedJobs)))
            element.appendChild(e)
        if self.data.LocalSuspendedJobs is not None:
            e = doc.createElement("LocalSuspendedJobs")
            e.appendChild(doc.createTextNode(str(self.data.LocalSuspendedJobs)))
            element.appendChild(e)
        if self.data.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(self.data.StagingJobs)))
            element.appendChild(e)
        if self.data.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.PreLRMSWaitingJobs)))
            element.appendChild(e)
        if self.data.EstimatedAverageWaitingTime is not None:
            e = doc.createElement("EstimatedAverageWaitingTime")
            e.appendChild(doc.createTextNode(str(self.data.EstimatedAverageWaitingTime)))
            element.appendChild(e)
        if self.data.EstimatedWorstWaitingTime is not None:
            e = doc.createElement("EstimatedWorstWaitingTime")
            e.appendChild(doc.createTextNode(str(self.data.EstimatedWorstWaitingTime)))
            element.appendChild(e)
        if self.data.FreeSlots is not None:
            e = doc.createElement("FreeSlots")
            e.appendChild(doc.createTextNode(str(self.data.FreeSlots)))
            element.appendChild(e)
        if self.data.FreeSlotsWithDuration is not None:
            e = doc.createElement("FreeSlotsWithDuration")
            e.appendChild(doc.createTextNode(self.data.FreeSlotsWithDuration))
            element.appendChild(e)
        if self.data.UsedSlots is not None:
            e = doc.createElement("UsedSlots")
            e.appendChild(doc.createTextNode(str(self.data.UsedSlots)))
            element.appendChild(e)
        if self.data.RequestedSlots is not None:
            e = doc.createElement("RequestedSlots")
            e.appendChild(doc.createTextNode(str(self.data.RequestedSlots)))
            element.appendChild(e)
        if self.data.ReservationPolicy is not None:
            e = doc.createElement("ReservationPolicy")
            e.appendChild(doc.createTextNode(self.data.ReservationPolicy))
            element.appendChild(e)
        for tag in self.data.Tag:
            e = doc.createElement("Tag")
            e.appendChild(doc.createTextNode(tag))
            element.appendChild(e)
        for endpoint in self.data.EndpointID:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(endpoint))
            element.appendChild(e)
        for environment in self.data.ResourceID:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(environment))
            element.appendChild(e)
        if self.data.ServiceID is not None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(self.data.ServiceID))
            element.appendChild(e)

#######################################################################################################################

class ComputingShareOgfJson(ShareOgfJson):
    data_cls = ComputingShare

    def __init__(self, data):
        ShareOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = ShareOgfJson.toJson(self)

        if self.data.MappingQueue is not None:
            doc["MappingQueue"] = self.data.MappingQueue
        if self.data.MaxWallTime is not None:
            doc["MaxWallTime"] = self.data.MaxWallTime
        if self.data.MaxMultiSlotWallTime is not None:
            doc["MaxMultiSlotWallTime"] = self.data.MaxMultiSlotWallTime
        if self.data.MinWallTime is not None:
            doc["MinWallTime"] = self.data.MinWallTime
        if self.data.DefaultWallTime is not None:
            doc["DefaultWallTime"] = self.data.DefaultWallTime
        if self.data.MaxCPUTime is not None:
            doc["MaxCPUTime"] = self.data.MaxCPUTime
        if self.data.MaxTotalCPUTime is not None:
            doc["MaxTotalCPUTime"] = self.data.MaxTotalCPUTime
        if self.data.MinCPUTime is not None:
            doc["MinCPUTime"] = self.data.MinCPUTime
        if self.data.DefaultCPUTime is not None:
            doc["DefaultCPUTime"] = self.data.DefaultCPUTime
        if self.data.MaxTotalJobs is not None:
            doc["MaxTotalJobs"] = self.data.MaxTotalJobs
        if self.data.MaxRunningJobs is not None:
            doc["MaxRunningJobs"] = self.data.MaxRunningJobs
        if self.data.MaxWaitingJobs is not None:
            doc["MaxWaitingJobs"] = self.data.MaxWaitingJobs
        if self.data.MaxPreLRMSWaitingJobs is not None:
            doc["MaxPreLRMSWaitingJobs"] = self.data.MaxPreLRMSWaitingJobs
        if self.data.MaxUserRunningJobs is not None:
            doc["MaxUserRunningJobs"] = self.data.MaxUserRunningJobs
        if self.data.MaxSlotsPerJob is not None:
            doc["MaxSlotsPerJob"] = self.data.MaxSlotsPerJob
        if self.data.MaxStageInStreams is not None:
            doc["MaxStageInStreams"] = self.data.MaxStageInStreams
        if self.data.MaxStageOutStreams is not None:
            doc["MaxStageOutStreams"] = self.data.MaxStageOutStreams
        if self.data.SchedulingPolicy is not None:
            doc["SchedulingPolicy"] = self.data.SchedulingPolicy
        if self.data.MaxMainMemory is not None:
            doc["MaxMainMemory"] = self.data.MaxMainMemory
        if self.data.GuaranteedMainMemory is not None:
            doc["GuaranteedMainMemory"] = self.data.GuaranteedMainMemory
        if self.data.MaxVirtualMemory is not None:
            doc["MaxVirtualMemory"] = self.data.MaxVirtualMemory
        if self.data.GuaranteedVirtualMemory is not None:
            doc["GuaranteedVirtualMemory"] = self.data.GuaranteedVirtualMemory
        if self.data.MaxDiskSpace is not None:
            doc["MaxDiskSpace"] = self.data.MaxDiskSpace
        if self.data.DefaultStorageService is not None:
            doc["DefaultStorageService"] = self.data.DefaultStorageService
        if self.data.Preemption is not None:
            doc["Preemption"] = self.data.Preemption
        doc["ServingState"] = self.data.ServingState
        if self.data.TotalJobs is not None:
            doc["TotalJobs"] = self.data.TotalJobs
        if self.data.RunningJobs is not None:
            doc["RunningJobs"] = self.data.RunningJobs
        if self.data.LocalRunningJobs is not None:
            doc["LocalRunningJobs"] = self.data.LocalRunningJobs
        if self.data.WaitingJobs is not None:
            doc["WaitingJobs"] = self.data.WaitingJobs
        if self.data.LocalWaitingJobs is not None:
            doc["LocalWaitingJobs"] = self.data.LocalWaitingJobs
        if self.data.SuspendedJobs is not None:
            doc["SuspendedJobs"] = self.data.SuspendedJobs
        if self.data.LocalSuspendedJobs is not None:
            doc["LocalSuspendedJobs"] = self.data.LocalSuspendedJobs
        if self.data.StagingJobs is not None:
            doc["StagingJobs"] = self.data.StagingJobs
        if self.data.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = self.data.PreLRMSWaitingJobs
        if self.data.EstimatedAverageWaitingTime is not None:
            doc["EstimatedAverageWaitingTime"] = self.data.EstimatedAverageWaitingTime
        if self.data.EstimatedWorstWaitingTime is not None:
            doc["EstimatedWorstWaitingTime"] = self.data.EstimatedWorstWaitingTime
        if self.data.FreeSlots is not None:
            doc["FreeSlots"] = self.data.FreeSlots
        if self.data.FreeSlotsWithDuration is not None:
            doc["FreeSlotsWithDuration"] = self.data.FreeSlotsWithDuration
        if self.data.UsedSlots is not None:
            doc["UsedSlots"] = self.data.UsedSlots
        #if self.data.UsedAcceleratorSlots is not None:
        #    doc["UsedAcceleratorSlots"] = self.data.UsedAcceleratorSlots
        if self.data.RequestedSlots is not None:
            doc["RequestedSlots"] = self.data.RequestedSlots
        if self.data.ReservationPolicy is not None:
            doc["ReservationPolicy"] = self.data.ReservationPolicy
        if len(self.data.Tag) > 0:
            doc["Tag"] = self.data.Tag
        if len(self.data.ComputingShareAccelInfoID) > 0:
            doc["Associations"]["ComputingShareAcceleratorInfo"]=self.data.ComputingShareAccelInfoID

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
        return self.toDom().toprettyxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for share in self.data.shares:
            sdoc = ComputingShareTeraGridXml(share).toDom()
            doc.documentElement.appendChild(sdoc.documentElement.firstChild)
        return doc

#######################################################################################################################

class ComputingSharesOgfJson(Representation):
    data_cls = ComputingShares

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        sdoc = []
        for share in self.data.shares:
            sdoc.append(ComputingShareOgfJson(share).toJson())
        return sdoc

#######################################################################################################################
