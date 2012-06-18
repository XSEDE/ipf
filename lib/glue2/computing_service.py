
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

from ipf.document import Document
from ipf.dt import *
from ipf.error import NoMoreInputsError,StepError

from glue2.computing_share import ComputingShare
from glue2.computing_endpoint import ComputingEndpoint
from glue2.step import GlueStep

#######################################################################################################################

class ComputingServiceStep(GlueStep):

    def __init__(self, params):
        GlueStep.__init__(self,params)

        self.name = "glue2/computing_service"
        self.description = "This step provides a GLUE 2 ComputingService document. It is an aggregation mechanism"
        self.time_out = 10
        self.requires_types = ["ipf/resource_name.txt",
                               "glue2/teragrid/computing_shares.json",
                               "glue2/teragrid/computing_endpoint.json"]
        self.produces_types = ["glue2/teragrid/computing_service.xml",
                               "glue2/teragrid/computing_service.json"]

        self.resource_name = None
        self.shares = None
        self.endpoints = None

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        self.resource_name = rn_doc.resource_name
        shares_doc = self._getInput("glue2/teragrid/computing_shares.json")
        self.shares = shares_doc.shares
        #endpoints_doc = self._getInput("glue2/teragrid/computing_endpoints.json")
        #self.endpoints = endpoints_doc.endpoints
        self.endpoints = []
        try:
            while True:
                endpoint_doc = self._getInput("glue2/teragrid/computing_endpoint.json")
                self.endpoints.append(endpoint_doc.endpoint)
        except NoMoreInputsError:
            pass

        service = self._run()

        service.ID = "urn:glue2:ComputingService:%s" % (self.resource_name)
        service.ComputingManager = "urn:glue2:ComputingManager:%s" % (self.resource_name)

        service._addShares(self.shares)
        service._addEndpoints(self.endpoints)

        for share in self.shares:
            share.ComputingService = service.ID
        for endpoint in self.endpoints:
            endpoint.ComputingService = service.ID

        if "glue2/teragrid/computing_service.xml" in self.requested_types:
            self.debug("sending output glue2/teragrid/computing_service.xml")
            self.output_queue.put(ComputingServiceDocumentXml(self.resource_name,service))
        if "glue2/teragrid/computing_service.json" in self.requested_types:
            self.debug("sending output glue2/teragrid/computing_service.json")
            self.output_queue.put(ComputingServiceDocumentJson(self.resource_name,service))

    def _run(self):
        self.error("ComputingServiceStep._run not overriden")
        raise StepError("ComputingServiceStep._run not overriden")

#######################################################################################################################

class ComputingServiceDocumentXml(Document):
    def __init__(self, resource_name, service):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_service.xml")
        self.service = service

    def _setBody(self, body):
        raise DocumentError("ComputingServiceDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        sdoc = self.service.toDom()
        doc.documentElement.appendChild(sdoc.documentElement.firstChild)
        #return doc.toxml()
        return doc.toprettyxml()

#######################################################################################################################

class ComputingServiceDocumentJson(Document):
    def __init__(self, resource_name, service):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_service.json")
        self.service = service

    def _setBody(self, body):
        raise DocumentError("ComputingServiceDocumentJson._setBody should parse the JSON...")

    def _getBody(self):
        doc = self.service.toJson()
        return json.dumps(doc,sort_keys=True,indent=4)

#######################################################################################################################

class ComputingService(object):
    def __init__(self):
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = 300
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
        #self.computingEndpoint = []    # list of ComputingEndpoint
        self.ComputingShare = []      # list of string (uri)
        self.ComputingManager = None  # string (uri)
        #self.computingManager = None   # ComputingManager (set by child class)
        self.StorageService = []       # list of string (uri)

    def _addShares(self, shares):
        self.ComputingShare = []
        if len(shares) == 0:
            return
        for share in shares:
            self.ComputingShare.append(share.ID)
            if share.TotalJobs is not None:
                if self.TotalJobs == None:
                    self.TotalJobs = 0
                self.TotalJobs = self.TotalJobs + share.TotalJobs
            if share.RunningJobs is not None:
                if self.RunningJobs == None:
                    self.RunningJobs = 0
                self.RunningJobs = self.RunningJobs + share.RunningJobs
            if share.WaitingJobs is not None:
                if self.WaitingJobs == None:
                    self.WaitingJobs = 0
                self.WaitingJobs = self.WaitingJobs + share.WaitingJobs
            if share.StagingJobs is not None:
                if self.StagingJobs == None:
                    self.StagingJobs = 0
                self.StagingJobs = self.StagingJobs + share.StagingJobs
            if share.SuspendedJobs is not None:
                if self.SuspendedJobs == None:
                    self.SuspendedJobs = 0
                self.SuspendedJobs = self.SuspendedJobs + share.SuspendedJobs
            if share.PreLRMSWaitingJobs is not None:
                if self.PreLRMSWaitingJobs == None:
                    self.PreLRMSWaitingJobs = 0
                self.PreLRMSWaitingJobs = self.PreLRMSWaitingJobs + share.PreLRMSWaitingJobs

    def _addEndpoints(self, endpoints):
        self.ComputingEndpoint = []
        for endpoint in endpoints:
            self.ComputingEndpoint.append(endpoint.ID)

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

        # Service
        for capability in self.Capability:
            e = doc.createElement("Capability")
            e.appendChild(doc.createTextNode(capability))
            root.appendChild(e)
        if self.Type is not None:
            e = doc.createElement("Type")
            e.appendChild(doc.createTextNode(self.Type))
            root.appendChild(e)
        if self.QualityLevel is not None:
            e = doc.createElement("QualityLevel")
            e.appendChild(doc.createTextNode(self.QualityLevel))
            root.appendChild(e)
        for status in self.StatusInfo:
            e = doc.createElement("StatusInfo")
            e.appendChild(doc.createTextNode(status))
            root.appendChild(e)
        if self.Complexity is not None:
            e = doc.createElement("Complexity")
            e.appendChild(doc.createTextNode(self.Complexity))
            root.appendChild(e)
        for endpoint in self.Endpoint:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for id in self.Share:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for contact in self.Contact:
            e = doc.createElement("Contact")
            e.appendChild(doc.createTextNode(contact))
            root.appendChild(e)
        if self.Location is not None:
            e = doc.createElement("Location")
            e.appendChild(doc.createTextNode(self.Location))
            root.appendChild(e)
        for id in self.Service:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)

        # ComputingService
        if self.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(self.TotalJobs)))
            root.appendChild(e)
        if self.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(self.RunningJobs)))
            root.appendChild(e)
        if self.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(self.WaitingJobs)))
            root.appendChild(e)
        if self.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(self.StagingJobs)))
            root.appendChild(e)
        if self.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(self.SuspendedJobs)))
            root.appendChild(e)
        if self.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.PreLRMSWaitingJobs)))
            root.appendChild(e)
        for id in self.ComputingEndpoint:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        for id in self.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(id))
            root.appendChild(e)
        if self.ComputingManager is not None:
            e = doc.createElement("ComputingManager")
            e.appendChild(doc.createTextNode(self.ComputingManager))
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

        # Service
        if len(self.Capability) > 0:
            doc["Capability"] = self.Capability
        if self.Type is not None:
            doc["Type"] = self.Type
        if self.QualityLevel is not None:
            doc["QualityLevel"] = self.QualityLevel
        if len(self.StatusInfo) > 0:
            doc["StatusInfo"] = self.StatusInfo
        if self.Complexity is not None:
            doc["Complexity"] = self.Complexity
        if len(self.Endpoint) > 0:
            doc["Endpoint"] = self.Endpoint
        if len(self.Share) > 0:
            doc["Share"] = self.Share
        if len(self.Contact) > 0:
            doc["Contact"] = self.Contact
        if self.Location is not None:
            doc["Location"] = self.Location
        if len(self.Service) > 0:
            doc["Service"] = self.Service

        # ComputingService
        if self.TotalJobs is not None:
            doc["TotalJobs"] = self.TotalJobs
        if self.RunningJobs is not None:
            doc["RunningJobs"] = self.RunningJobs
        if self.WaitingJobs is not None:
            doc["WaitingJobs"] = self.WaitingJobs
        if self.StagingJobs is not None:
            doc["StagingJobs"] = self.StagingJobs
        if self.SuspendedJobs is not None:
            doc["SuspendedJobs"] = self.SuspendedJobs
        if self.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = self.PreLRMSWaitingJobs
        if len(self.ComputingEndpoint) > 0:
            doc["ComputingEndpoint"] = self.ComputingEndpoint
        if len(self.ComputingShare) > 0:
            doc["ComputingShare"] = self.ComputingShare
        if self.ComputingManager is not None:
            doc["ComputingManager"] = self.ComputingManager

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

    ###################################################################################################################

    def toXml(self, indent=""):
        mstr = indent+"<ComputingService"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                  Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name is not None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"++"'>"+self.Extension[key]+"</Extension>\n"

        # Service
        for capability in self.Capability:
            mstr = mstr+indent+"  <Capability>"+capability+"</Capability>\n"
        if self.Type is not None:
            mstr = mstr+indent+"  <Type>"+self.Type+"</Type>\n"
        if self.QualityLevel is not None:
            mstr = mstr+indent+"  <QualityLevel>"+self.QualityLevel+"</QualityLevel>\n"
        for status in self.StatusInfo:
            mstr = mstr+indent+"  <StatusInfo>"+status+"</StatusInfo>\n"
        if self.Complexity is not None:
            mstr = mstr+indent+"  <Complexity>"+self.Complexity+"</Complexity>\n"
        for endpoint in self.Endpoint:
            mstr = mstr+indent+"  <Endpoint>"+endpoint+"</Endpoint>\n"
        for share in self.Share:
            mstr = mstr+indent+"  <Share>"+Share+"</Share>\n"
        for contact in self.Contact:
            mstr = mstr+indent+"  <Contact>"+contact+"</Contact>\n"
        if self.Location is not None:
            mstr = mstr+indent+"  <Location>"+self.Location+"</Location>\n"
        for service in self.Service:
            mstr = mstr+indent+"  <Service>"+Service+"</Service>\n"

        # ComputingService
        if self.TotalJobs is not None:
            mstr = mstr+indent+"  <TotalJobs>"+str(self.TotalJobs)+"</TotalJobs>\n"
        if self.RunningJobs is not None:
            mstr = mstr+indent+"  <RunningJobs>"+str(self.RunningJobs)+"</RunningJobs>\n"
        if self.WaitingJobs is not None:
            mstr = mstr+indent+"  <WaitingJobs>"+str(self.WaitingJobs)+"</WaitingJobs>\n"
        if self.StagingJobs is not None:
            mstr = mstr+indent+"  <StagingJobs>"+str(self.StagingJobs)+"</StagingJobs>\n"
        if self.SuspendedJobs is not None:
            mstr = mstr+indent+"  <SuspendedJobs>"+str(self.SuspendedJobs)+"</SuspendedJobs>\n"
        if self.PreLRMSWaitingJobs is not None:
            mstr = mstr+indent+"  <PreLRMSWaitingJobs>"+str(self.PreLRMSWaitingJobs)+"</PreLRMSWaitingJobs>\n"
        for id in self.ComputingEndpoint:
            mstr = mstr+indent+"  <ComputingEndpoint>"+id+"</ComputingEndpoint>\n"
        for id in self.ComputingShare:
            mstr = mstr+indent+"  <ComputingShare>"+id+"</ComputingShare>\n"
        if self.ComputingManager is not None:
            mstr = mstr+indent+"  <ComputingManager>"+self.ComputingManager+"</ComputingManager>\n"

        mstr = mstr+indent+"</ComputingService>\n"
        return mstr
