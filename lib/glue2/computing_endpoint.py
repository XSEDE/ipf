
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

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.resource_name import ResourceName

from glue2.step import GlueStep

#######################################################################################################################

class ComputingEndpointStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step produces one or more documents containing one or more GLUE 2 ComputingEndpoint."
        self.time_out = 10
        self.requires = [ResourceName]
        self.produces = [ComputingEndpoint]

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name

        endpoints = self._run()

        for i in range(0,len(endpoints)):
            if endpoints[i].Name == None:
                endpoints[i].Name = "endpoint-%d" % (i+1)
        for endpoint in endpoints:
            endpoint.id = "%s.%s" % (endpoint.Name,self.resource_name)
            endpoint.ID = "urn:glue2:ComputingEndpoint:%s.%s" % (endpoint.Name,self.resource_name)
            endpoint.ComputingService = "urn:glue2:ComputingService:%s" % (self.resource_name)

            self._output(endpoint)

    def _run(self):
        raise StepError("ComputingEndpointStep._run not overriden")

#######################################################################################################################

class ParamComputingEndpointStep(ComputingEndpointStep):
    def __init__(self):
        ComputingEndpointStep.__init__(self)

        self.description = "create a ComputingEndpoint using parameters"
        self._acceptParameter("endpoint",
                              "An endpoint, represented as a dictionary. See ComputingEndpoint.fromJson() for the keys and values.",
                              True)

    def _run(self):
        try:
            endpoint_doc = self.params["endpoint"]
        except KeyError:
            raise StepError("endpoint not specified")
        endpoint = ComputingEndpoint()
        endpoint.fromJson(endpoint_doc)
        return [endpoint]

#######################################################################################################################

class ComputingEndpoint(Data):

    DEFAULT_VALIDITY = 3600 # seconds

    def __init__(self):
        Data.__init__(self)

        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = ComputingEndpoint.DEFAULT_VALIDITY
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

    def fromJson(self, doc):
        # Entity
        if "CreationTime" in doc:
            self.CreationTime = textToDateTime(doc["CreationTime"])
        else:
            self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = doc.get("Validity",ComputingEndpoint.DEFAULT_VALIDITY)
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

#######################################################################################################################

class ComputingEndpointTeraGridXml(Representation):
    data_cls = ComputingEndpoint

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)
        self.hide = hide

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(endpoint):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingEndpoint")
        doc.documentElement.appendChild(root)

        # Entity
        e = doc.createElement("CreationTime")
        e.appendChild(doc.createTextNode(dateTimeToText(endpoint.CreationTime)))
        e.setAttribute("Validity",str(endpoint.Validity))
        root.appendChild(e)

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(endpoint.ID))
        root.appendChild(e)

        if endpoint.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(endpoint.Name))
            root.appendChild(e)
        for info in endpoint.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        for key in endpoint.Extension:
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(endpoint.Extension[key]))
            root.appendChild(e)

        # Endpoint
        if endpoint.URL is not None:
            e = doc.createElement("URL")
            e.appendChild(doc.createTextNode(endpoint.URL))
            root.appendChild(e)
        for capability in endpoint.Capability:
            e = doc.createElement("Capability")
            e.appendChild(doc.createTextNode(capability))
            root.appendChild(e)
        if endpoint.Technology is not None:
            e = doc.createElement("Technology")
            e.appendChild(doc.createTextNode(endpoint.Technology))
            root.appendChild(e)
        if endpoint.InterfaceName is not None:
            e = doc.createElement("InterfaceName")
            e.appendChild(doc.createTextNode(endpoint.InterfaceName))
            root.appendChild(e)
        if endpoint.InterfaceVersion is not None:
            e = doc.createElement("InterfaceVersion")
            e.appendChild(doc.createTextNode(endpoint.InterfaceVersion))
            root.appendChild(e)
        for extension in endpoint.InterfaceExtension:
            e = doc.createElement("InterfaceExtension")
            e.appendChild(doc.createTextNode(extension))
            root.appendChild(e)
        for wsdl in endpoint.WSDL:
            e = doc.createElement("WSDL")
            e.appendChild(doc.createTextNode(wsdl))
            root.appendChild(e)
        for profile in endpoint.SupportedProfile:
            e = doc.createElement("SupportedProfile")
            e.appendChild(doc.createTextNode(endpoint.profile))
            root.appendChild(e)
        for semantics in endpoint.Semantics:
            e = doc.createElement("Semantics")
            e.appendChild(doc.createTextNode(semantics))
            root.appendChild(e)
        if endpoint.Implementor is not None:
            e = doc.createElement("Implementor")
            e.appendChild(doc.createTextNode(endpoint.Implementor))
            root.appendChild(e)
        if endpoint.ImplementationName is not None:
            e = doc.createElement("ImplementationName")
            e.appendChild(doc.createTextNode(endpoint.ImplementationName))
            root.appendChild(e)
        if endpoint.ImplementationVersion is not None:
            e = doc.createElement("ImplementationVersion")
            e.appendChild(doc.createTextNode(endpoint.ImplementationVersion))
            root.appendChild(e)
        if endpoint.QualityLevel is not None:
            e = doc.createElement("QualityLevel")
            e.appendChild(doc.createTextNode(endpoint.QualityLevel))
            root.appendChild(e)
        if endpoint.HealthState is not None:
            e = doc.createElement("HealthState")
            e.appendChild(doc.createTextNode(endpoint.HealthState))
            root.appendChild(e)
        if endpoint.HealthStateInfo is not None:
            e = doc.createElement("HealthStateInfo")
            e.appendChild(doc.createTextNode(endpoint.HealthStateInfo))
            root.appendChild(e)
        if endpoint.ServingState is not None:
            e = doc.createElement("ServingState")
            e.appendChild(doc.createTextNode(endpoint.ServingState))
            root.appendChild(e)
        if endpoint.StartTime is not None:
            e = doc.createElement("StartTime")
            e.appendChild(doc.createTextNode(dateTimeToText(endpoint.StartTime)))
            root.appendChild(e)
        if endpoint.IssuerCA is not None:
            e = doc.createElement("IssuerCA")
            e.appendChild(doc.createTextNode(endpoint.IssuerCA))
            root.appendChild(e)
        for trustedCA in endpoint.TrustedCA:
            e = doc.createElement("TrustedCA")
            e.appendChild(doc.createTextNode(trustedCA))
            root.appendChild(e)
        if endpoint.DowntimeAnnounce is not None:
            e = doc.createElement("DowntimeAnnounce")
            e.appendChild(doc.createTextNode(dateTimeToText(endpoint.DowntimeAnnounce)))
            root.appendChild(e)
        if endpoint.DowntimeStart is not None:
            e = doc.createElement("DowntimeStart")
            e.appendChild(doc.createTextNode(dateTimeToText(endpoint.DowntimeStart)))
            root.appendChild(e)
        if endpoint.DowntimeEnd is not None:
            e = doc.createElement("DowntimeEnd")
            e.appendChild(doc.createTextNode(dateTimeToText(endpoint.DowntimeEnd)))
            root.appendChild(e)
        if endpoint.DowntimeInfo is not None:
            e = doc.createElement("DowntimeInfo")
            e.appendChild(doc.createTextNode(endpoint.DowntimeInfo))
            root.appendChild(e)

        # ComputingEndpoint
        if endpoint.Staging is not None:
            e = doc.createElement("Staging")
            e.appendChild(doc.createTextNode(endpoint.Staging))
            root.appendChild(e)
        for description in endpoint.JobDescription:
            e = doc.createElement("JobDescription")
            e.appendChild(doc.createTextNode(description))
            root.appendChild(e)
        if endpoint.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(endpoint.TotalJobs)))
            root.appendChild(e)
        if endpoint.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(endpoint.RunningJobs)))
            root.appendChild(e)
        if endpoint.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(endpoint.WaitingJobs)))
            root.appendChild(e)
        if endpoint.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(endpoint.StagingJobs)))
            root.appendChild(e)
        if endpoint.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(endpoint.SuspendedJobs)))
            root.appendChild(e)
        if endpoint.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(endpoint.PreLRMSWaitingJobs)))
            root.appendChild(e)
        if endpoint.ComputingService is not None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(endpoint.ComputingService))
            root.appendChild(e)
        for share in  endpoint.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for activity in  endpoint.ComputingActivity:
            e = doc.createElement("ComputingActivity")
            e.appendChild(doc.createTextNode(activity))
            root.appendChild(e)

        return doc

#######################################################################################################################

class ComputingEndpointIpfJson(Representation):
    data_cls = ComputingEndpoint

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(endpoint):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(endpoint.CreationTime)
        doc["Validity"] = endpoint.Validity
        doc["ID"] = endpoint.ID
        if endpoint.Name is not None:
            doc["Name"] = endpoint.Name
        if len(endpoint.OtherInfo) > 0:
            doc["OtherInfo"] = endpoint.OtherInfo
        if len(endpoint.Extension) > 0:
            doc["Extension"] = endpoint.Extension

        # Endpoint
        if endpoint.URL is not None:
            doc["URL"] = endpoint.URL
        if len(endpoint.Capability) > 0:
            doc["Capability"] = endpoint.Capability
        if endpoint.Technology is not None:
            doc["Technology"] = endpoint.Technology
        if endpoint.InterfaceName is not None:
            doc["InterfaceName"] = endpoint.InterfaceName
        if endpoint.InterfaceVersion is not None:
            doc["InterfaceVersion"] = endpoint.InterfaceVersion
        if len(endpoint.InterfaceExtension) > 0:
            doc["InterfaceExtension"] = endpoint.InterfaceExtension
        if len(endpoint.WSDL) > 0:
            doc["WSDL"] = endpoint.WSDL
        if len(endpoint.SupportedProfile) > 0:
            doc["SupportedProfile"] = endpoint.SupportedProfile
        if len(endpoint.Semantics) > 0:
            doc["Semantics"] = endpoint.Semantics
        if endpoint.Implementor is not None:
            doc["Implementor"] = endpoint.Implementor
        if endpoint.ImplementationName is not None:
            doc["ImplementationName"] = endpoint.ImplementationName
        if endpoint.ImplementationVersion is not None:
            doc["ImplementationVersion"] = endpoint.ImplementationVersion
        if endpoint.QualityLevel is not None:
            doc["QualityLevel"] = endpoint.QualityLevel
        if endpoint.HealthState is not None:
            doc["HealthState"] = endpoint.HealthState
        if endpoint.HealthStateInfo is not None:
            doc["HealthStateInfo"] = endpoint.HealthStateInfo
        if endpoint.ServingState is not None:
            doc["ServingState"] = endpoint.ServingState
        if endpoint.StartTime is not None:
            doc["StartTime"] = dateTimeToText(endpoint.StartTime)
        if endpoint.IssuerCA is not None:
            doc["IssuerCA"] = endpoint.IssuerCA
        if len(endpoint.TrustedCA) > 0:
            doc["TrustedCA"] = endpoint.TrustedCA
        if endpoint.DowntimeAnnounce is not None:
            doc["DowntimeAnnounce"] = dateTimeToText(endpoint.DowntimeAnnounce)
        if endpoint.DowntimeStart is not None:
            doc["DowntimeStart"] = dateTimeToText(endpoint.DowntimeStart)
        if endpoint.DowntimeEnd is not None:
            doc["DowntimeEnd"] = dateTimeToText(endpoint.DowntimeEnd)
        if endpoint.DowntimeInfo is not None:
            doc["DowntimeInfo"] = endpoint.DowntimeInfo

        # ComputingEndpoint
        if endpoint.Staging is not None:
            doc["Staging"] = endpoint.Staging
        if len(endpoint.JobDescription) > 0:
            doc["JobDescription"] = endpoint.JobDescription
        if endpoint.TotalJobs is not None:
            doc["TotalJobs"] = endpoint.TotalJobs
        if endpoint.RunningJobs is not None:
            doc["RunningJobs"] = endpoint.RunningJobs
        if endpoint.WaitingJobs is not None:
            doc["WaitingJobs"] = endpoint.WaitingJobs
        if endpoint.StagingJobs is not None:
            doc["StagingJobs"] = endpoint.StagingJobs
        if endpoint.SuspendedJobs is not None:
            doc["SuspendedJobs"] = endpoint.SuspendedJobs
        if endpoint.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = endpoint.PreLRMSWaitingJobs
        if endpoint.ComputingService is not None:
            doc["ComputingService"] = endpoint.ComputingService
        if len(endpoint.ComputingShare) > 0:
            doc["ComputingShare"] = endpoint.ComputingShare
        if len(endpoint.ComputingActivity) > 0:
            doc["ComputingActivity"] = endpoint.ComputingActivity

        return doc

#######################################################################################################################
