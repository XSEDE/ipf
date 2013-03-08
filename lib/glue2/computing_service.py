
###############################################################################
#   Copyright 2009-2012 The University of Texas at Austin                     #
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
from ipf.error import NoMoreInputsError,StepError
from ipf.sysinfo import ResourceName

from glue2.computing_activity import ComputingActivity, ComputingActivities
from glue2.computing_share import ComputingShares
from glue2.computing_endpoint import ComputingEndpoint
from glue2.location import Location
from glue2.step import GlueStep

#######################################################################################################################

class ComputingServiceStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step provides a GLUE 2 ComputingService document. It is an aggregation mechanism"
        self.time_out = 10
        self.requires = [ResourceName,Location,ComputingActivities,ComputingShares,ComputingEndpoint]
        self.produces = [ComputingService]

        self.resource_name = None
        self.location = None
        self.activities = None
        self.shares = None
        self.endpoints = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.location = self._getInput(Location).ID
        self.activities = self._getInput(ComputingActivities).activities
        self.shares = self._getInput(ComputingShares).shares
        self.endpoints = []
        try:
            while True:
                self.endpoints.append(self._getInput(ComputingEndpoint))
        except NoMoreInputsError:
            pass

        service = self._run()

        service.id = self.resource_name
        service.ID = "urn:glue2:ComputingService:%s" % (self.resource_name)
        service.Location = self.location
        service.ComputingManager = "urn:glue2:ComputingManager:%s" % (self.resource_name)


        service._addActivities(self.activities)
        service._addShares(self.shares)
        service._addEndpoints(self.endpoints)

        for share in self.shares:
            share.ComputingService = service.ID
        for endpoint in self.endpoints:
            endpoint.ComputingService = service.ID

        self._output(service)

    def _run(self):
        raise StepError("ComputingServiceStep._run not overriden")

#######################################################################################################################

class ComputingService(Data):
    def __init__(self):
        Data.__init__(self)
        
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = None
        self.ID = None
        self.Name = None
        self.OtherInfo = [] # strings
        self.Extension = {} # (key,value) strings

        # Service
        self.Capability = None   # string (Capability)
        self.Type = None         # string (ServiceType)
        self.QualityLevel = None # string (QualityLevel)
        self.StatusInfo = []     # list of string (uri)
        self.Complexity = None   # string
        self.Endpoint = []       # list of string (uri)
        self.Share = []          # list of string (LocalID)
        self.Contact = []        # list of string (uri)
        self.Location = None     # string (uri)
        self.Service = []        # list of string (uri)

        # ComputingService
        self.TotalJobs = None          # integer
        self.RunningJobs = None        # integer
        self.WaitingJobs = None        # integer
        self.StagingJobs = None        # integer
        self.SuspendedJobs = None      # integer
        self.PreLRMSWaitingJobs = None # integer
        self.ComputingEndpoint = []   # list of string (uri)
        self.ComputingShare = []      # list of string (uri)
        self.ComputingManager = None  # string (uri)
        self.StorageService = []       # list of string (uri)

    def _addActivities(self, activities):
        self.RunningJobs = 0
        self.WaitingJobs = 0
        self.StagingJobs = 0
        self.SuspendedJobs = 0
        self.PreLRMSWaitingJobs = 0
        for activity in activities:
            if activity.State == ComputingActivity.STATE_RUNNING:
                self.RunningJobs = self.RunningJobs + 1
            elif activity.State == ComputingActivity.STATE_PENDING:
                self.WaitingJobs = self.WaitingJobs + 1
            elif activity.State == ComputingActivity.STATE_HELD:
                self.WaitingJobs = self.WaitingJobs + 1
            else:
                # output a warning
                pass
        self.TotalJobs = self.RunningJobs + self.WaitingJobs + self.StagingJobs + self.SuspendedJobs + \
                         self.PreLRMSWaitingJobs

    def _addShares(self, shares):
        self.ComputingShare = []
        if len(shares) == 0:
            return
        for share in shares:
            self.ComputingShare.append(share.ID)

    def _addEndpoints(self, endpoints):
        self.ComputingEndpoint = []
        for endpoint in endpoints:
            self.ComputingEndpoint.append(endpoint.ID)

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

        # Service
        self.Capability = doc.get("Capability",[])
        self.Type = doc.get("Type")
        self.QualityLevel = doc.get("QualityLevel")
        self.StatusInfo = doc.get("StatusInfo",[])
        self.Complexity = doc.get("Complexity")
        self.Endpoint = doc.get("Endpoint",[])
        self.Share = doc.get("Share",[])
        self.Contact = doc.get("Contact",[])
        self.Location = doc.get("Location")
        self.Serice = doc.get("Service",[])

        # ComputingService
        self.TotalJobs = doc.get("TotalJobs")
        self.RunningJobs = doc.get("RunningJobs")
        self.WaitingJobs = doc.get("WaitingJobs")
        self.StagingJobs = doc.get("StagingJobs")
        self.SuspendedJobs = doc.get("SuspendedJobs")
        self.PreLRMSWaitingJobs = doc.get("PreLRMSWaitingJobs")
        self.ComputingEndpoint = doc.get("ComputingEndpoint",[])
        self.ComputingShare = doc.get("ComputingShare",[])
        self.ComputingManager = doc.get("ComputingManager")

#######################################################################################################################

class ComputingServiceTeraGridXml(Representation):
    data_cls = ComputingService

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(service):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingService")
        doc.documentElement.appendChild(root)

        # Entity
        e = doc.createElement("CreationTime")
        e.appendChild(doc.createTextNode(dateTimeToText(service.CreationTime)))
        if service.Validity is not None:
            e.setAttribute("Validity",str(service.Validity))
        root.appendChild(e)

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(service.ID))
        root.appendChild(e)

        if service.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(service.Name))
            root.appendChild(e)
        for info in service.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        for key in service.Extension.keys():
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(service.Extension[key]))
            root.appendChild(e)

        # Service
        for capability in service.Capability:
            e = doc.createElement("Capability")
            e.appendChild(doc.createTextNode(capability))
            root.appendChild(e)
        if service.Type is not None:
            e = doc.createElement("Type")
            e.appendChild(doc.createTextNode(service.Type))
            root.appendChild(e)
        if service.QualityLevel is not None:
            e = doc.createElement("QualityLevel")
            e.appendChild(doc.createTextNode(service.QualityLevel))
            root.appendChild(e)
        for status in service.StatusInfo:
            e = doc.createElement("StatusInfo")
            e.appendChild(doc.createTextNode(status))
            root.appendChild(e)
        if service.Complexity is not None:
            e = doc.createElement("Complexity")
            e.appendChild(doc.createTextNode(service.Complexity))
            root.appendChild(e)
        for endpoint in service.Endpoint:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for id in service.Share:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for contact in service.Contact:
            e = doc.createElement("Contact")
            e.appendChild(doc.createTextNode(contact))
            root.appendChild(e)
        if service.Location is not None:
            e = doc.createElement("Location")
            e.appendChild(doc.createTextNode(service.Location))
            root.appendChild(e)
        for id in service.Service:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)

        # ComputingService
        if service.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(service.TotalJobs)))
            root.appendChild(e)
        if service.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(service.RunningJobs)))
            root.appendChild(e)
        if service.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(service.WaitingJobs)))
            root.appendChild(e)
        if service.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(service.StagingJobs)))
            root.appendChild(e)
        if service.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(service.SuspendedJobs)))
            root.appendChild(e)
        if service.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(service.PreLRMSWaitingJobs)))
            root.appendChild(e)
        for id in service.ComputingEndpoint:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for id in service.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        if service.ComputingManager is not None:
            e = doc.createElement("ComputingManager")
            e.appendChild(doc.createTextNode(service.ComputingManager))
            root.appendChild(e)

        return doc

#######################################################################################################################

class ComputingServiceIpfJson(Representation):
    data_cls = ComputingService

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(service):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(service.CreationTime)
        if service.Validity is not None:
            doc["Validity"] = service.Validity
        doc["ID"] = service.ID
        if service.Name is not None:
            doc["Name"] = service.Name
        if len(service.OtherInfo) > 0:
            doc["OtherInfo"] = service.OtherInfo
        if len(service.Extension) > 0:
            doc["Extension"] = service.Extension

        # Service
        if len(service.Capability) > 0:
            doc["Capability"] = service.Capability
        if service.Type is not None:
            doc["Type"] = service.Type
        if service.QualityLevel is not None:
            doc["QualityLevel"] = service.QualityLevel
        if len(service.StatusInfo) > 0:
            doc["StatusInfo"] = service.StatusInfo
        if service.Complexity is not None:
            doc["Complexity"] = service.Complexity
        if len(service.Endpoint) > 0:
            doc["Endpoint"] = service.Endpoint
        if len(service.Share) > 0:
            doc["Share"] = service.Share
        if len(service.Contact) > 0:
            doc["Contact"] = service.Contact
        if service.Location is not None:
            doc["Location"] = service.Location
        if len(service.Service) > 0:
            doc["Service"] = service.Service

        # ComputingService
        if service.TotalJobs is not None:
            doc["TotalJobs"] = service.TotalJobs
        if service.RunningJobs is not None:
            doc["RunningJobs"] = service.RunningJobs
        if service.WaitingJobs is not None:
            doc["WaitingJobs"] = service.WaitingJobs
        if service.StagingJobs is not None:
            doc["StagingJobs"] = service.StagingJobs
        if service.SuspendedJobs is not None:
            doc["SuspendedJobs"] = service.SuspendedJobs
        if service.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = service.PreLRMSWaitingJobs
        if len(service.ComputingEndpoint) > 0:
            doc["ComputingEndpoint"] = service.ComputingEndpoint
        if len(service.ComputingShare) > 0:
            doc["ComputingShare"] = service.ComputingShare
        if service.ComputingManager is not None:
            doc["ComputingManager"] = service.ComputingManager

        return doc

#######################################################################################################################
