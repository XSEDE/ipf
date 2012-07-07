
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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
import ConfigParser

from ipf.document import Document
from ipf.dt import *
from ipf.error import StepError

from glue2.step import GlueStep

#######################################################################################################################

class ComputingEndpointStep(GlueStep):
    def __init__(self, params):
        GlueStep.__init__(self,params)

        self.name = "glue2/computing_endpoint"
        self.description = "This step produces one or more documents containing one or more GLUE 2 ComputingEndpoint."
        self.time_out = 10
        self.requires_types = ["ipf/resource_name.txt"]
        self.produces_types = ["glue2/teragrid/computing_endpoint.xml",
                               "glue2/teragrid/computing_endpoint.json"]

        self.resource_name = None

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        self.resource_name = rn_doc.resource_name

        endpoints = self._run()
        for i in range(0,len(endpoints)):
            if endpoints[i].Name == None:
                endpoint[i].Name = "endpoint-%d" % (i+1)
        for endpoint in endpoints:
            endpoint.ID = "urn:glue2:ComputingEndpoint:%s.%s" % (endpoint.Name,self.resource_name)
            endpoint.ComputingService = "urn:glue2:ComputingService:%s" % (self.resource_name)

            self._output(ComputingEndpointDocumentXml(self.resource_name,endpoint))
            self._output(ComputingEndpointDocumentJson(self.resource_name,endpoint))

    def _run(self):
        raise StepError("ComputingEndpointStep._run not overriden")

#######################################################################################################################

class ParamComputingEndpointStep(ComputingEndpointStep):
    def __init__(self, params):
        ComputingEndpointStep.__init__(self,params)
        self.name = "glue2/param/computing_endpoint"
        self.description = "create a ComputingEndpoint using parameters"
        self.accepts_params["endpoint"] = "An endpoint, represented as a dictionary. See ComputingEndpoint.fromJson() for the keys and values."

    def _run(self):
        try:
            endpoint_doc = self.params["endpoint"]
        except KeyError:
            raise StepError("endpoint not specified")
        endpoint = ComputingEndpoint()
        endpoint.fromJson(endpoint_doc)
        return [endpoint]

#######################################################################################################################

class ComputingEndpointDocumentXml(Document):
    def __init__(self, resource_name, endpoint):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_endpoint.xml")
        self.endpoint = endpoint

    def _setBody(self, body):
        raise DocumentError("ComputingEndpointDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        edoc = endpoint.toDom()
        doc.documentElement.appendChild(edoc.documentElement.firstChild)
        #return doc.toxml()
        return doc.toprettyxml()

#######################################################################################################################

class ComputingEndpointDocumentJson(Document):
    def __init__(self, resource_name, endpoint):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_endpoint.json")
        self.endpoint = endpoint

    def _setBody(self, body):
        raise DocumentError("ComputingEndpointDocumentJson._setBody should parse the JSON...")

    def _getBody(self):
        return json.dumps(endpoint.toJson(),sort_keys=True,indent=4)

#######################################################################################################################

class ComputingEndpoint(object):
    def __init__(self):
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = 300
        self.ID = None      # string (uri)
        self.Name = None    # string
        self.OtherInfo = [] # list of string
        self.Extension = {} # (key,value) strings

        # Endpoint
        self.URL = None                   # string (uri)
        self.Capability = []              # list of string (Capability)
        self.Technology = "unknown"       # string (EndpointTechnology)
        self.InterfaceName = "unknown"    # string (InterfaceName)
        self.InterfaceVersion = None      # string
        self.InterfaceExtension = []      # list of string (uri)
        self.WSDL = []                    # list of string (uri)
        self.SupportedProfile = []        # list of string (uri)
        self.Semantics = []               # list of string (uri)
        self.Implementor = None           # string
        self.ImplementationName = None    # string
        self.ImplementationVersion = None # string
        self.QualityLevel = None          # string (QualityLevel)
        self.HealthState = "unknown"      # string (EndpointHealthState)
        self.HealthStateInfo = None       # string
        self.ServingState = "production"  # string (ServingState)
        self.StartTime = None             # datetime
        self.IssuerCA = None              # string (DN)
        self.TrustedCA = []               # list of string (DN)
        self.DowntimeAnnounce = None      # datetime
        self.DowntimeStart = None         # datetime
        self.DowntimeEnd = None           # datetime
        self.DowntimeInfo = None          # string

        # ComputingEndpoint
        self.Staging = None            # string (Staging)
        self.JobDescription = []       # list of string (JobDescription)
        self.TotalJobs = None          # integer
        self.RunningJobs = None        # integer
        self.WaitingJobs = None        # integer
        self.StagingJobs = None        # integer
        self.SuspendedJobs = None      # integer
        self.PreLRMSWaitingJobs = None # integer
        self.ComputingService = None   # string (uri)
        self.ComputingShare = []       # list of string (uri)
        self.ComputingActivity = []    # list of string (uri)
    
    ###################################################################################################################

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingEndpoint")
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
            e.appendChild(doc.createTextNode(self.Extension[key]))
            root.appendChild(e)

        # Endpoint
        if self.URL is not None:
            e = doc.createElement("URL")
            e.appendChild(doc.createTextNode(self.URL))
            root.appendChild(e)
        for capability in self.Capability:
            e = doc.createElement("Capability")
            e.appendChild(doc.createTextNode(capability))
            root.appendChild(e)
        if self.Technology is not None:
            e = doc.createElement("Technology")
            e.appendChild(doc.createTextNode(self.Technology))
            root.appendChild(e)
        if self.InterfaceName is not None:
            e = doc.createElement("InterfaceName")
            e.appendChild(doc.createTextNode(self.InterfaceName))
            root.appendChild(e)
        if self.InterfaceVersion is not None:
            e = doc.createElement("InterfaceVersion")
            e.appendChild(doc.createTextNode(self.InterfaceVersion))
            root.appendChild(e)
        for extension in self.InterfaceExtension:
            e = doc.createElement("InterfaceExtension")
            e.appendChild(doc.createTextNode(extension))
            root.appendChild(e)
        for wsdl in self.WSDL:
            e = doc.createElement("WSDL")
            e.appendChild(doc.createTextNode(wsdl))
            root.appendChild(e)
        for profile in self.SupportedProfile:
            e = doc.createElement("SupportedProfile")
            e.appendChild(doc.createTextNode(self.profile))
            root.appendChild(e)
        for semantics in self.Semantics:
            e = doc.createElement("Semantics")
            e.appendChild(doc.createTextNode(semantics))
            root.appendChild(e)
        if self.Implementor is not None:
            e = doc.createElement("Implementor")
            e.appendChild(doc.createTextNode(self.Implementor))
            root.appendChild(e)
        if self.ImplementationName is not None:
            e = doc.createElement("ImplementationName")
            e.appendChild(doc.createTextNode(self.ImplementationName))
            root.appendChild(e)
        if self.ImplementationVersion is not None:
            e = doc.createElement("ImplementationVersion")
            e.appendChild(doc.createTextNode(self.ImplementationVersion))
            root.appendChild(e)
        if self.QualityLevel is not None:
            e = doc.createElement("QualityLevel")
            e.appendChild(doc.createTextNode(self.QualityLevel))
            root.appendChild(e)
        if self.HealthState is not None:
            e = doc.createElement("HealthState")
            e.appendChild(doc.createTextNode(self.HealthState))
            root.appendChild(e)
        if self.HealthStateInfo is not None:
            e = doc.createElement("HealthStateInfo")
            e.appendChild(doc.createTextNode(self.HealthStateInfo))
            root.appendChild(e)
        if self.ServingState is not None:
            e = doc.createElement("ServingState")
            e.appendChild(doc.createTextNode(self.ServingState))
            root.appendChild(e)
        if self.StartTime is not None:
            e = doc.createElement("StartTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.StartTime)))
            root.appendChild(e)
        if self.IssuerCA is not None:
            e = doc.createElement("IssuerCA")
            e.appendChild(doc.createTextNode(self.IssuerCA))
            root.appendChild(e)
        for trustedCA in self.TrustedCA:
            e = doc.createElement("TrustedCA")
            e.appendChild(doc.createTextNode(trustedCA))
            root.appendChild(e)
        if self.DowntimeAnnounce is not None:
            e = doc.createElement("DowntimeAnnounce")
            e.appendChild(doc.createTextNode(dateTimeToText(self.DowntimeAnnounce)))
            root.appendChild(e)
        if self.DowntimeStart is not None:
            e = doc.createElement("DowntimeStart")
            e.appendChild(doc.createTextNode(dateTimeToText(self.DowntimeStart)))
            root.appendChild(e)
        if self.DowntimeEnd is not None:
            e = doc.createElement("DowntimeEnd")
            e.appendChild(doc.createTextNode(dateTimeToText(self.DowntimeEnd)))
            root.appendChild(e)
        if self.DowntimeInfo is not None:
            e = doc.createElement("DowntimeInfo")
            e.appendChild(doc.createTextNode(self.DowntimeInfo))
            root.appendChild(e)

        # ComputingEndpoint
        if self.Staging is not None:
            e = doc.createElement("Staging")
            e.appendChild(doc.createTextNode(self.Staging))
            root.appendChild(e)
        for description in self.JobDescription:
            e = doc.createElement("JobDescription")
            e.appendChild(doc.createTextNode(description))
            root.appendChild(e)
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
        if self.ComputingService is not None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(self.ComputingService))
            root.appendChild(e)
        for share in  self.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for activity in  self.ComputingActivity:
            e = doc.createElement("ComputingActivity")
            e.appendChild(doc.createTextNode(activity))
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

        # Endpoint
        if self.URL is not None:
            doc["URL"] = self.URL
        if len(self.Capability) > 0:
            doc["Capability"] = self.Capability
        if self.Technology is not None:
            doc["Technology"] = self.Technology
        if self.InterfaceName is not None:
            doc["InterfaceName"] = self.InterfaceName
        if self.InterfaceVersion is not None:
            doc["InterfaceVersion"] = self.InterfaceVersion
        if len(self.InterfaceExtension) > 0:
            doc["InterfaceExtension"] = self.InterfaceExtension
        if len(self.WSDL) > 0:
            doc["WSDL"] = self.WSDL
        if len(self.SupportedProfile) > 0:
            doc["SupportedProfile"] = self.SupportedProfile
        if len(self.Semantics) > 0:
            doc["Semantics"] = self.Semantics
        if self.Implementor is not None:
            doc["Implementor"] = self.Implementor
        if self.ImplementationName is not None:
            doc["ImplementationName"] = self.ImplementationName
        if self.ImplementationVersion is not None:
            doc["ImplementationVersion"] = self.ImplementationVersion
        if self.QualityLevel is not None:
            doc["QualityLevel"] = self.QualityLevel
        if self.HealthState is not None:
            doc["HealthState"] = self.HealthState
        if self.HealthStateInfo is not None:
            doc["HealthStateInfo"] = self.HealthStateInfo
        if self.ServingState is not None:
            doc["ServingState"] = self.ServingState
        if self.StartTime is not None:
            doc["StartTime"] = dateTimeToText(self.StartTime)
        if self.IssuerCA is not None:
            doc["IssuerCA"] = self.IssuerCA
        if len(self.TrustedCA) > 0:
            doc["TrustedCA"] = self.TrustedCA
        if self.DowntimeAnnounce is not None:
            doc["DowntimeAnnounce"] = dateTimeToText(self.DowntimeAnnounce)
        if self.DowntimeStart is not None:
            doc["DowntimeStart"] = dateTimeToText(self.DowntimeStart)
        if self.DowntimeEnd is not None:
            doc["DowntimeEnd"] = dateTimeToText(self.DowntimeEnd)
        if self.DowntimeInfo is not None:
            doc["DowntimeInfo"] = self.DowntimeInfo

        # ComputingEndpoint
        if self.Staging is not None:
            doc["Staging"] = self.Staging
        if len(self.JobDescription) > 0:
            doc["JobDescription"] = self.JobDescription
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
        if self.ComputingService is not None:
            doc["ComputingService"] = self.ComputingService
        if len(self.ComputingShare) > 0:
            doc["ComputingShare"] = self.ComputingShare
        if len(self.ComputingActivity) > 0:
            doc["ComputingActivity"] = self.ComputingActivity

        return doc
    
    ###################################################################################################################

    def fromJson(self, doc):
        # Entity
        if "CreationTime" in doc:
            self.CreationTime = textToDateTime(doc["CreationTime"])
        else:
            self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = doc.get("Validity")
        self.ID = doc.get("ID")
        self.Name = doc.get("Name")
        self.OtherInfo = doc.get("OtherInfo",[])
        self.Extension = doc.get("Extension",{})

        # Endpoint
        self.URL = doc.get("URL")
        self.Capability = doc.get("Capability",[])
        self.Technology = doc.get("Technology")
        self.InterfaceName = doc.get("InterfaceName")
        self.InterfaceVersion = doc.get("InterfaceVersion")
        self.InterfaceExtension = doc.get("InterfaceExtension",[])
        self.WSDL = doc.get("WSDL",[])
        self.SupportedProfile = doc.get("SupportedProfile",[])
        self.Semantics = doc.get("Semantics",[])
        self.Implementor = doc.get("Implementor")
        self.ImplementationName = doc.get("ImplementationName")
        self.ImplementationVersion = doc.get("ImplementationVersion")
        self.QualityLevel = doc.get("QualityLevel")
        self.HealthState = doc.get("HealthState")
        self.HealthStateInfo = doc.get("HealthStateInfo")
        self.StartTime = textToDateTime(doc.get("StartTime"))
        self.IssuerCA = doc.get("IssuerCA")
        self.TrustedCA = doc.get("TrustedCA",[])
        self.DowntimeAnnounce = textToDateTime(doc.get("DowntimeAnnounce"))
        self.DowntimeStart = textToDateTime(doc.get("DowntimeStart"))
        self.DowntimeEnd = textToDateTime(doc.get("DowntimeEnd"))
        self.DowntimeInfo = doc.get("DowntimeInfo")

        # ComputingEndpoint
        self.Staging = doc.get("Staging")
        self.JobDescription = doc.get("JobDescription",[])
        self.TotalJobs = doc.get("TotalJobs")
        self.RunningJobs = doc.get("RunningJobs")
        self.WaitingJobs = doc.get("WaitingJobs")
        self.StagingJobs = doc.get("StagingJobs")
        self.PreLRMSWaitingJobs = doc.get("PreLRMSWaitingJobs")
        self.ComputingService = doc.get("ComputingService")
        self.ComputingShare = doc.get("ComputingShare",[])
        self.ComputingActivity = doc.get("ComputingActivity",[])

    ###################################################################################################################

    def toXml(self, indent=""):
        mstr = indent+"<ComputingEndpoint"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                   Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name is not None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"++"'>"+self.Extension[key]+"</Extension>\n"

        # Endpoint
        if self.URL is not None:
            mstr = mstr+indent+"  <URL>"+self.URL+"</URL>\n"
        for capability in self.Capability:
            mstr = mstr+indent+"  <Capability>"+capability+"</Capability>\n"
        if self.Technology is not None:
            mstr = mstr+indent+"  <Technology>"+self.Technology+"</Technology>\n"
        if self.InterfaceName is not None:
            mstr = mstr+indent+"  <InterfaceName>"+self.InterfaceName+"</InterfaceName>\n"
        if self.InterfaceVersion is not None:
            mstr = mstr+indent+"  <InterfaceVersion>"+self.InterfaceVersion+"</InterfaceVersion>\n"
        for extension in self.InterfaceExtension:
            mstr = mstr+indent+"  <InterfaceExtension>"+extension+"</InterfaceExtension>\n"
        for wsdl in self.WSDL:
            mstr = mstr+indent+"  <WSDL>"+wsdl+"</WSDL>\n"
        for profile in self.SupportedProfile:
            mstr = mstr+indent+"  <SupportedProfile>"+profile+"</SupportedProfile>\n"
        for semantics in self.Semantics:
            mstr = mstr+indent+"  <Semantics>"+semantics+"</Semantics>\n"
        if self.Implementor is not None:
            mstr = mstr+indent+"  <Implementor>"+self.Implementor+"</Implementor>\n"
        if self.ImplementationName is not None:
            mstr = mstr+indent+"  <ImplementationName>"+self.ImplementationName+"</ImplementationName>\n"
        if self.ImplementationVersion is not None:
            mstr = mstr+indent+"  <ImplementationVersion>"+self.ImplementationVersion+"</ImplementationVersion>\n"
        if self.QualityLevel is not None:
            mstr = mstr+indent+"  <QualityLevel>"+self.QualityLevel+"</QualityLevel>\n"
        if self.HealthState is not None:
            mstr = mstr+indent+"  <HealthState>"+self.HealthState+"</HealthState>\n"
        if self.HealthStateInfo is not None:
            mstr = mstr+indent+"  <HealthStateInfo>"+self.HealthStateInfo+"</HealthStateInfo>\n" # ?
        if self.ServingState is not None:
            mstr = mstr+indent+"  <ServingState>"+self.ServingState+"</ServingState>\n"
        if self.StartTime is not None:
            mstr = mstr+indent+"  <StartTime>"+self.StartTime+"</StartTime>\n"
        if self.IssuerCA is not None:
            mstr = mstr+indent+"  <IssuerCA>"+self.IssuerCA+"</IssuerCA>\n"
        for trustedCA in self.TrustedCA:
            mstr = mstr+indent+"  <TrustedCA>"+trustedCA+"</TrustedCA>\n"
        if self.DowntimeAnnounce is not None:
            mstr = mstr+indent+"  <DowntimeAnnounce>"+self.DowntimeAnnounce+"</DowntimeAnnounce>\n"
        if self.DowntimeStart is not None:
            mstr = mstr+indent+"  <DowntimeStart>"+self.DowntimeStart+"</DowntimeStart>\n"
        if self.DowntimeEnd is not None:
            mstr = mstr+indent+"  <DowntimeEnd>"+self.DowntimeEnd+"</DowntimeEnd>\n"
        if self.DowntimeInfo is not None:
            mstr = mstr+indent+"  <DowntimeInfo>"+self.DowntimeInfo+"</DowntimeInfo>\n"

        # ComputingEndpoint
        if self.Staging is not None:
            mstr = mstr+indent+"  <Staging>"+self.Staging+"</Staging>\n"
        for description in self.JobDescription:
            mstr = mstr+indent+"  <JobDescription>"+description+"</JobDescription>\n"
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
        if self.ComputingService is not None:
            mstr = mstr+indent+"  <ComputingService>"+self.ComputingService+"</ComputingService>\n"
        for share in  self.ComputingShare:
            mstr = mstr+indent+"  <ComputingShare>"+share+"</ComputingShare>\n"
        for activity in  self.ComputingActivity:
            mstr = mstr+indent+"  <ComputingActivity>"+activity+"</ComputingActivity>\n"
        mstr = mstr+indent+"</ComputingEndpoint>\n"

        return mstr
