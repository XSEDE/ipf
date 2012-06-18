
###############################################################################
#   Copyright 2011-2012 The University of Texas at Austin                     #
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
from ipf.error import StepError

from glue2.computing_activity import ComputingActivity
from glue2.step import GlueStep

#######################################################################################################################

class ComputingSharesStep(GlueStep):

    def __init__(self, params):
        GlueStep.__init__(self,params)

        self.name = "glue2/computing_shares"
        self.description = "produces a document containing one or more GLUE 2 ComputingShare"
        self.time_out = 30
        self.requires_types = ["ipf/resource_name.txt",
                               "glue2/teragrid/computing_activities.json"]
        self.produces_types = ["glue2/teragrid/computing_shares.xml",
                               "glue2/teragrid/computing_shares.json"]
        self.accepts_params["queues"] = "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. the expression is processed in order and the value for a queue at the end determines if it is shown."

        self.resource_name = None
        self.activities = None
        
    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        self.resource_name = rn_doc.resource_name
        activities_doc = self._getInput("glue2/teragrid/computing_activities.json")
        self.activities = activities_doc.activities

        shares = self._run()

        for share in shares:
            share.ID = "urn:glue2:ComputingShare:%s.%s" % (share.MappingQueue,self.resource_name)
            share.ComputingService = "urn:glue2:ComputingService:%s" % (self.resource_name)

        self._addActivities(shares)

        if "glue2/teragrid/computing_shares.xml" in self.requested_types:
            self.debug("sending output glue2/teragrid/computing_shares.xml")
            self.output_queue.put(ComputingSharesDocumentXml(self.resource_name,shares))
        if "glue2/teragrid/computing_shares.json" in self.requested_types:
            self.debug("sending output glue2/teragrid/computing_shares.json")
            self.output_queue.put(ComputingSharesDocumentJson(self.resource_name,shares))

    def _run(self):
        self.error("ComputingSharesStep._run not overriden")
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
            #print(str(activity))
            share = shareDict.get(activity.Queue)
            if share == None:
                self.warning("  didn't find share for queue "+str(activity.Queue))
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

#######################################################################################################################

class ComputingSharesDocumentXml(Document):
    def __init__(self, resource_name, shares):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_shares.xml")
        self.shares = shares

    def _setBody(self, body):
        raise DocumentError("ComputingSharesDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for share in self.shares:
            sdoc = share.toDom()
            doc.documentElement.appendChild(sdoc.documentElement.firstChild)
        #return doc.toxml()
        return doc.toprettyxml()

#######################################################################################################################

class ComputingSharesDocumentJson(Document):
    def __init__(self, resource_name, shares):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_shares.json")
        self.shares = shares

    def _setBody(self, body):
        raise DocumentError("ComputingSharesDocumentJson._setBody should parse the JSON...")

    def _getBody(self):
        sdoc = []
        for share in self.shares:
            sdoc.append(share.toJson())
        return json.dumps(sdoc,sort_keys=True,indent=4)

#######################################################################################################################

class ComputingShare(object):
    def __init__(self):
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = 300
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

    ###################################################################################################################

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingShare")
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
        for key in self.Extension:
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(str(self.Extension[key])))
            root.appendChild(e)

        # Share
        if self.Description is not None:
            e = doc.createElement("Description")
            e.appendChild(doc.createTextNode(self.Description))
            root.appendChild(e)
        for endpoint in self.Endpoint:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for resource in self.Resource:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(resource))
            root.appendChild(e)
        if self.Service is not None:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(self.Service))
            root.appendChild(e)
        for activity in self.Activity:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(activity))
            root.appendChild(e)
        for policy in self.MappingPolicy:
            e = doc.createElement("MappingPolicy")
            e.appendChild(doc.createTextNode(policy))
            root.appendChild(e)

        # ComputingShare
        if self.MappingQueue is not None:
            e = doc.createElement("MappingQueue")
            e.appendChild(doc.createTextNode(self.MappingQueue))
            root.appendChild(e)
        if self.MaxWallTime is not None:
            e = doc.createElement("MaxWallTime")
            e.appendChild(doc.createTextNode(str(self.MaxWallTime)))
            root.appendChild(e)
        if self.MaxMultiSlotWallTime is not None:
            e = doc.createElement("MaxMultiSlotWallTime")
            e.appendChild(doc.createTextNode(str(self.MaxMultiSlotWallTime)))
            root.appendChild(e)
        if self.MinWallTime is not None:
            e = doc.createElement("MinWallTime")
            e.appendChild(doc.createTextNode(str(self.MinWallTime)))
            root.appendChild(e)
        if self.DefaultWallTime is not None:
            e = doc.createElement("DefaultWallTime")
            e.appendChild(doc.createTextNode(str(self.DefaultWallTime)))
            root.appendChild(e)
        if self.MaxCPUTime is not None:
            e = doc.createElement("MaxCPUTime")
            e.appendChild(doc.createTextNode(str(self.MaxCPUTime)))
            root.appendChild(e)
        if self.MaxTotalCPUTime is not None:
            e = doc.createElement("MaxTotalCPUTime")
            e.appendChild(doc.createTextNode(str(self.MaxTotalCPUTime)))
            root.appendChild(e)
        if self.MinCPUTime is not None:
            e = doc.createElement("MinCPUTime")
            e.appendChild(doc.createTextNode(str(self.MinCPUTime)))
            root.appendChild(e)
        if self.DefaultCPUTime is not None:
            e = doc.createElement("DefaultCPUTime")
            e.appendChild(doc.createTextNode(str(self.DefaultCPUTime)))
            root.appendChild(e)
        if self.MaxTotalJobs is not None:
            e = doc.createElement("MaxTotalJobs")
            e.appendChild(doc.createTextNode(str(self.MaxTotalJobs)))
            root.appendChild(e)
        if self.MaxRunningJobs is not None:
            e = doc.createElement("MaxRunningJobs")
            e.appendChild(doc.createTextNode(str(self.MaxRunningJobs)))
            root.appendChild(e)
        if self.MaxWaitingJobs is not None:
            e = doc.createElement("MaxWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.MaxWaitingJobs)))
            root.appendChild(e)
        if self.MaxPreLRMSWaitingJobs is not None:
            e = doc.createElement("MaxPreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.MaxPreLRMSWaitingJobs)))
            root.appendChild(e)
        if self.MaxUserRunningJobs is not None:
            e = doc.createElement("MaxUserRunningJobs")
            e.appendChild(doc.createTextNode(str(self.MaxUserRunningJobs)))
            root.appendChild(e)
        if self.MaxSlotsPerJob is not None:
            e = doc.createElement("MaxSlotsPerJob")
            e.appendChild(doc.createTextNode(str(self.MaxSlotsPerJob)))
            root.appendChild(e)
        if self.MaxStageInStreams is not None:
            e = doc.createElement("MaxStageInStreams")
            e.appendChild(doc.createTextNode(str(self.MaxStageInStreams)))
            root.appendChild(e)
        if self.MaxStageOutStreams is not None:
            e = doc.createElement("MaxStageOutStreams")
            e.appendChild(doc.createTextNode(str(self.MaxStageOutStreams)))
            root.appendChild(e)
        if self.SchedulingPolicy is not None:
            e = doc.createElement("SchedulingPolicy")
            e.appendChild(doc.createTextNode(self.SchedulingPolicy))
            root.appendChild(e)
        if self.MaxMainMemory is not None:
            e = doc.createElement("MaxMainMemory")
            e.appendChild(doc.createTextNode(str(self.MaxMainMemory)))
            root.appendChild(e)
        if self.GuaranteedMainMemory is not None:
            e = doc.createElement("GuaranteedMainMemory")
            e.appendChild(doc.createTextNode(str(self.GuaranteedMainMemory)))
            root.appendChild(e)
        if self.MaxVirtualMemory is not None:
            e = doc.createElement("MaxVirtualMemory")
            e.appendChild(doc.createTextNode(str(self.MaxVirtualMemory)))
            root.appendChild(e)
        if self.GuaranteedVirtualMemory is not None:
            e = doc.createElement("GuaranteedVirtualMemory")
            e.appendChild(doc.createTextNode(str(self.GuaranteedVirtualMemory)))
            root.appendChild(e)
        if self.MaxDiskSpace is not None:
            e = doc.createElement("MaxDiskSpace")
            e.appendChild(doc.createTextNode(str(self.MaxDiskSpace)))
            root.appendChild(e)
        if self.DefaultStorageService is not None:
            e = doc.createElement("DefaultStorageService")
            e.appendChild(doc.createTextNode(self.DefaultStorageService))
            root.appendChild(e)
        if self.Preemption is not None:
            e = doc.createElement("Preemption")
            if self.Preemption:
                e.appendChild(doc.createTextNode("true"))
            else:
                e.appendChild(doc.createTextNode("false"))
            root.appendChild(e)
        if self.ServingState is not None:
            e = doc.createElement("ServingState")
            e.appendChild(doc.createTextNode(self.ServingState))
            root.appendChild(e)
        if self.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(self.TotalJobs)))
            root.appendChild(e)
        if self.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(self.RunningJobs)))
            root.appendChild(e)
        if self.LocalRunningJobs is not None:
            e = doc.createElement("LocalRunningJobs")
            e.appendChild(doc.createTextNode(str(self.LocalRunningJobs)))
            root.appendChild(e)
        if self.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(self.WaitingJobs)))
            root.appendChild(e)
        if self.LocalWaitingJobs is not None:
            e = doc.createElement("LocalWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.LocalWaitingJobs)))
            root.appendChild(e)
        if self.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(self.SuspendedJobs)))
            root.appendChild(e)
        if self.LocalSuspendedJobs is not None:
            e = doc.createElement("LocalSuspendedJobs")
            e.appendChild(doc.createTextNode(str(self.LocalSuspendedJobs)))
            root.appendChild(e)
        if self.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(self.StagingJobs)))
            root.appendChild(e)
        if self.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.PreLRMSWaitingJobs)))
            root.appendChild(e)
        if self.EstimatedAverageWaitingTime is not None:
            e = doc.createElement("EstimatedAverageWaitingTime")
            e.appendChild(doc.createTextNode(str(self.EstimatedAverageWaitingTime)))
            root.appendChild(e)
        if self.EstimatedWorstWaitingTime is not None:
            e = doc.createElement("EstimatedWorstWaitingTime")
            e.appendChild(doc.createTextNode(str(self.EstimatedWorstWaitingTime)))
            root.appendChild(e)
        if self.FreeSlots is not None:
            e = doc.createElement("FreeSlots")
            e.appendChild(doc.createTextNode(str(self.FreeSlots)))
            root.appendChild(e)
        if self.FreeSlotsWithDuration is not None:
            e = doc.createElement("FreeSlotsWithDuration")
            e.appendChild(doc.createTextNode(self.FreeSlotsWithDuration))
            root.appendChild(e)
        if self.UsedSlots is not None:
            e = doc.createElement("UsedSlots")
            e.appendChild(doc.createTextNode(str(self.UsedSlots)))
            root.appendChild(e)
        if self.RequestedSlots is not None:
            e = doc.createElement("RequestedSlots")
            e.appendChild(doc.createTextNode(str(self.RequestedSlots)))
            root.appendChild(e)
        if self.ReservationPolicy is not None:
            e = doc.createElement("ReservationPolicy")
            e.appendChild(doc.createTextNode(self.Service))
            root.appendChild(e)
        for tag in self.Tag:
            e = doc.createElement("Tag")
            e.appendChild(doc.createTextNode(tag))
            root.appendChild(e)
        for endpoint in self.ComputingEndpoint:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for environment in self.ExecutionEnvironment:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(environment))
            root.appendChild(e)
        if self.ComputingService is not None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(self.ComputingService))
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

        # Share
        if self.Description is not None:
            doc["Description"] = self.Description
        if len(self.Endpoint) > 0:
            doc["Endpoint"] = self.Endpoint
        if len(self.Resource) > 0:
            doc["Resource"] = self.Resource
        if self.Service is not None:
            doc["Service"] = self.Service
        if len(self.Activity) > 0:
            doc["Activity"] = self.Activity
        if len(self.MappingPolicy) > 0:
            doc["MappingPolicy"] = self.MappingPolicy

        # ComputingShare
        if self.MappingQueue is not None:
            doc["MappingQueue"] = self.MappingQueue
        if self.MaxWallTime is not None:
            doc["MaxWallTime"] = self.MaxWallTime
        if self.MaxMultiSlotWallTime is not None:
            doc["MaxMultiSlotWallTime"] = self.MaxMultiSlotWallTime
        if self.MinWallTime is not None:
            doc["MinWallTime"] = self.MinWallTime
        if self.DefaultWallTime is not None:
            doc["DefaultWallTime"] = self.DefaultWallTime
        if self.MaxCPUTime is not None:
            doc["MaxCPUTime"] = self.MaxCPUTime
        if self.MaxTotalCPUTime is not None:
            doc["MaxTotalCPUTime"] = self.MaxTotalCPUTime
        if self.MinCPUTime is not None:
            doc["MinCPUTime"] = self.MinCPUTime
        if self.DefaultCPUTime is not None:
            doc["DefaultCPUTime"] = self.DefaultCPUTime
        if self.MaxTotalJobs is not None:
            doc["MaxTotalJobs"] = self.MaxTotalJobs
        if self.MaxRunningJobs is not None:
            doc["MaxRunningJobs"] = self.MaxRunningJobs
        if self.MaxWaitingJobs is not None:
            doc["MaxWaitingJobs"] = self.MaxWaitingJobs
        if self.MaxPreLRMSWaitingJobs is not None:
            doc["MaxPreLRMSWaitingJobs"] = self.MaxPreLRMSWaitingJobs
        if self.MaxUserRunningJobs is not None:
            doc["MaxUserRunningJobs"] = self.MaxUserRunningJobs
        if self.MaxSlotsPerJob is not None:
            doc["MaxSlotsPerJob"] = self.MaxSlotsPerJob
        if self.MaxStageInStreams is not None:
            doc["MaxStageInStreams"] = self.MaxStageInStreams
        if self.MaxStageOutStreams is not None:
            doc["MaxStageOutStreams"] = self.MaxStageOutStreams
        if self.SchedulingPolicy is not None:
            doc["SchedulingPolicy"] = self.SchedulingPolicy
        if self.MaxMainMemory is not None:
            doc["MaxMainMemory"] = self.MaxMainMemory
        if self.GuaranteedMainMemory is not None:
            doc["GuaranteedMainMemory"] = self.GuaranteedMainMemory
        if self.MaxVirtualMemory is not None:
            doc["MaxVirtualMemory"] = self.MaxVirtualMemory
        if self.GuaranteedVirtualMemory is not None:
            doc["GuaranteedVirtualMemory"] = self.GuaranteedVirtualMemory
        if self.MaxDiskSpace is not None:
            doc["MaxDiskSpace"] = self.MaxDiskSpace
        if self.DefaultStorageService is not None:
            doc["DefaultStorageService"] = self.DefaultStorageService
        if self.Preemption is not None:
            doc["Preemption"] = self.Preemption
        if self.ServingState is not None:
            doc["ServingState"] = self.ServingState
        if self.TotalJobs is not None:
            doc["TotalJobs"] = self.TotalJobs
        if self.RunningJobs is not None:
            doc["RunningJobs"] = self.RunningJobs
        if self.LocalRunningJobs is not None:
            doc["LocalRunningJobs"] = self.LocalRunningJobs
        if self.WaitingJobs is not None:
            doc["WaitingJobs"] = self.WaitingJobs
        if self.LocalWaitingJobs is not None:
            doc["LocalWaitingJobs"] = self.LocalWaitingJobs
        if self.SuspendedJobs is not None:
            doc["SuspendedJobs"] = self.SuspendedJobs
        if self.LocalSuspendedJobs is not None:
            doc["LocalSuspendedJobs"] = self.LocalSuspendedJobs
        if self.StagingJobs is not None:
            doc["StagingJobs"] = self.StagingJobs
        if self.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = self.PreLRMSWaitingJobs
        if self.EstimatedAverageWaitingTime is not None:
            doc["EstimatedAverageWaitingTime"] = self.EstimatedAverageWaitingTime
        if self.EstimatedWorstWaitingTime is not None:
            doc["EstimatedWorstWaitingTime"] = self.EstimatedWorstWaitingTime
        if self.FreeSlots is not None:
            doc["FreeSlots"] = self.FreeSlots
        if self.FreeSlotsWithDuration is not None:
            doc["FreeSlotsWithDuration"] = self.FreeSlotsWithDuration
        if self.UsedSlots is not None:
            doc["UsedSlots"] = self.UsedSlots
        if self.RequestedSlots is not None:
            doc["RequestedSlots"] = self.RequestedSlots
        if self.ReservationPolicy is not None:
            doc["ReservationPolicy"] = self.ReservationPolicy
        if len(self.Tag) > 0:
            doc["Tag"] = self.Tag
        if len(self.ComputingEndpoint):
            doc["ComputingEndpoint"] = self.ComputingEndpoint
        if len(self.ExecutionEnvironment):
            doc["ExecutionEnvironment"] = self.ExecutionEnvironment
        if self.ComputingService is not None:
            doc["ComputingService"] = self.ComputingService

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

    ###################################################################################################################

    def toXml(self, indent=""):
        mstr = indent+"<ComputingShare"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name is not None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension:
            mstr = mstr+indent+"  <Extension Key='"+key+"'>"+str(self.Extension[key])+"</Extension>\n"

        # Share
        if self.Description is not None:
            mstr = mstr+indent+"  <Description>"+self.Description+"</Description>\n"
        for endpoint in self.Endpoint:
            mstr = mstr+indent+"  <Endpoint>"+endpoint+"</Endpoint>\n"
        for resource in self.Resource:
            mstr = mstr+indent+"  <Resource>"+resource+"</Resource>\n"
        if self.Service is not None:
            mstr = mstr+indent+"  <Service>"+self.Service+"</Service>\n"
        for activity in self.Activity:
            mstr = mstr+indent+"  <Activity>"+activity+"</Activity>\n"
        for policy in self.MappingPolicy:
            mstr = mstr+indent+"  <MappingPolicy>"+policy+"</MappingPolicy>\n"

        # ComputingShare
        if self.MappingQueue is not None:
            mstr = mstr+indent+"  <MappingQueue>"+self.MappingQueue+"</MappingQueue>\n"
        if self.MaxWallTime is not None:
            mstr = mstr+indent+"  <MaxWallTime>"+str(self.MaxWallTime)+"</MaxWallTime>\n"
        if self.MaxMultiSlotWallTime is not None:
            mstr = mstr+indent+"  <MaxTotalWallTime>"+str(self.MaxTotalWallTime)+"</MaxTotalWallTime>\n"
        if self.MinWallTime is not None:
            mstr = mstr+indent+"  <MinWallTime>"+str(self.MinWallTime)+"</MinWallTime>\n"
        if self.DefaultWallTime is not None:
            mstr = mstr+indent+"  <DefaultWallTime>"+str(self.DefaultWallTime)+"</DefaultWallTime>\n"
        if self.MaxCPUTime is not None:
            mstr = mstr+indent+"  <MaxCPUTime>"+str(self.MaxCPUTime)+"</MaxCPUTime>\n"
        if self.MaxTotalCPUTime is not None:
            mstr = mstr+indent+"  <MaxTotalCPUTime>"+str(self.MaxTotalCPUTime)+"</MaxTotalCPUTime>\n"
        if self.MinCPUTime is not None:
            mstr = mstr+indent+"  <MinCPUTime>"+str(self.MinCPUTime)+"</MinCPUTime>\n"
        if self.DefaultCPUTime is not None:
            mstr = mstr+indent+"  <DefaultCPUTime>"+str(self.DefaultCPUTime)+"</DefaultCPUTime>\n"
        if self.MaxTotalJobs is not None:
            mstr = mstr+indent+"  <MaxTotalJobs>"+str(self.MaxTotalJobs)+"</MaxTotalJobs>\n"
        if self.MaxRunningJobs is not None:
            mstr = mstr+indent+"  <MaxRunningJobs>"+str(self.MaxRunningJobs)+"</MaxRunningJobs>\n"
        if self.MaxWaitingJobs is not None:
            mstr = mstr+indent+"  <MaxWaitingJobs>"+str(self.MaxWaitingJobs)+"</MaxWaitingJobs>\n"
        if self.MaxPreLRMSWaitingJobs is not None:
            mstr = mstr+indent+"  <MaxPreLRMSWaitingJobs>"+str(self.MaxPreLRMSWaitingJobs)+ \
                   "</MaxPreLRMSWaitingJobs>\n"
        if self.MaxUserRunningJobs is not None:
            mstr = mstr+indent+"  <MaxUserRunningJobs>"+str(self.MaxUserRunningJobs)+"</MaxUserRunningJobs>\n"
        if self.MaxSlotsPerJob is not None:
            mstr = mstr+indent+"  <MaxSlotsPerJob>"+str(self.MaxSlotsPerJob)+"</MaxSlotsPerJob>\n"
        if self.MaxStageInStreams is not None:
            mstr = mstr+indent+"  <MaxStageInStreams>"+str(self.MaxStageInStreams)+"</MaxStageInStreams>\n"
        if self.MaxStageOutStreams is not None:
            mstr = mstr+indent+"  <MaxStageOutStreams>"+str(self.MaxStageOutStreams)+"</MaxStageOutStreams>\n"
        if self.SchedulingPolicy is not None:
            mstr = mstr+indent+"  <SchedulingPolicy>"+self.SchedulingPolicy+"</SchedulingPolicy>\n"
        if self.MaxMainMemory is not None:
            mstr = mstr+indent+"  <MaxMainMemory>"+str(self.MaxMainMemory)+"</MaxMainMemory>\n"
        if self.GuaranteedMainMemory is not None:
            mstr = mstr+indent+"  <GuaranteedMainMemory>"+str(self.GuaranteedMainMemory)+"</GuaranteedMainMemory>\n"
        if self.MaxVirtualMemory is not None:
            mstr = mstr+indent+"  <MaxVirtualMemory>"+str(self.MaxVirtualMemory)+"</MaxVirtualMemory>\n"
        if self.GuaranteedVirtualMemory is not None:
            mstr = mstr+indent+"  <GuaranteedVirtualMemory>"+str(self.GuaranteedVirtualMemory)+ \
                   "</GuaranteedVirtualMemory>\n"
        if self.MaxDiskSpace is not None:
            mstr = mstr+indent+"  <MaxDiskSpace>"+str(self.MaxDiskSpace)+"</MaxDiskSpace>\n"
        if self.DefaultStorageService is not None:
            mstr = mstr+indent+"  <DefaultStorageService>"+self.DefaultStorageService+"</DefaultStorageService>\n"
        if self.Preemption is not None:
            if self.Preemption:
                mstr = mstr+indent+"  <Preemption>true</Preemption>\n"
            else:
                mstr = mstr+indent+"  <Preemption>false</Preemption>\n"
        if self.ServingState is not None:
            mstr = mstr+indent+"  <ServingState>"+self.ServingState+"</ServingState>\n"
        if self.TotalJobs is not None:
            mstr = mstr+indent+"  <TotalJobs>"+str(self.TotalJobs)+"</TotalJobs>\n"
        if self.RunningJobs is not None:
            mstr = mstr+indent+"  <RunningJobs>"+str(self.RunningJobs)+"</RunningJobs>\n"
        if self.LocalRunningJobs is not None:
            mstr = mstr+indent+"  <LocalRunningJobs>"+str(self.LocalRunningJobs)+"</LocalRunningJobs>\n"
        if self.WaitingJobs is not None:
            mstr = mstr+indent+"  <WaitingJobs>"+str(self.WaitingJobs)+"</WaitingJobs>\n"
        if self.LocalWaitingJobs is not None:
            mstr = mstr+indent+"  <LocalWaitingJobs>"+str(self.LocalWaitingJobs)+"</LocalWaitingJobs>\n"
        if self.SuspendedJobs is not None:
            mstr = mstr+indent+"  <SuspendedJobs>"+str(self.SuspendedJobs)+"</SuspendedJobs>\n"
        if self.LocalSuspendedJobs is not None:
            mstr = mstr+indent+"  <LocalSuspendedJobs>"+str(self.LocalSuspendedJobs)+"</LocalSuspendedJobs>\n"
        if self.StagingJobs is not None:
            mstr = mstr+indent+"  <StagingJobs>"+str(self.StagingJobs)+"</StagingJobs>\n"
        if self.PreLRMSWaitingJobs is not None:
            mstr = mstr+indent+"  <PreLRMSWaitingJobs>"+str(self.PreLRMSWaitingJobs)+"</PreLRMSWaitingJobs>\n"
        if self.EstimatedAverageWaitingTime is not None:
            mstr = mstr+indent+"  <EstimatedAverageWaitingTime>"+str(self.EstimatedAverageWaitingTime)+ \
                   "  </EstimatedAverageWaitingTime>\n"
        if self.EstimatedWorstWaitingTime is not None:
            mstr = mstr+indent+"  <EstimatedWorstWaitingTime>"+str(self.EstimatedWorstWaitingTime)+ \
                   "  </EstimatedWorstWaitingTime>\n"
        if self.FreeSlots is not None:
            mstr = mstr+indent+"  <FreeSlots>"+str(self.FreeSlots)+"</FreeSlots>\n"
        if self.FreeSlotsWithDuration is not None:
            mstr = mstr+indent+"  <FreeSlotsWithDuration>"+str(self.FreeSlotsWithDuration)+ \
                   "</FreeSlotsWithDuration>\n"
        if self.UsedSlots is not None:
            mstr = mstr+indent+"  <UsedSlots>"+str(self.UsedSlots)+"</UsedSlots>\n"
        if self.RequestedSlots is not None:
            mstr = mstr+indent+"  <RequestedSlots>"+str(self.RequestedSlots)+"</RequestedSlots>\n"
        if self.ReservationPolicy is not None:
            mstr = mstr+indent+"  <ReservationPolicy>"+str(self.ReservationPolicy)+"</ReservationPolicy>\n"
        for tag in self.Tag:
            mstr = mstr+indent+"  <Tag>"+tag+"</Tag>\n"
        for endpoint in self.ComputingEndpoint:
            mstr = mstr+indent+"  <ComputingEndpoint>"+endpoint+"</ComputingEndpoint>\n"
        for environment in self.ExecutionEnvironment:
            mstr = mstr+indent+"  <ExecutionEnvironment>"+environment+"</ExecutionEnvironment>\n"
        if self.ComputingService is not None:
            mstr = mstr+indent+"  <ComputingService>"+str(self.ComputingService)+"</ComputingService>\n"
        # not outputting activity info for privacy/security
        #for activity in self.computingActivity:
        #    mstr = mstr+indent+"  <ComputingActivity>"+activity.ID+"</ComputingActivity>\n"
        mstr = mstr+indent+"</ComputingShare>\n"

        return mstr
