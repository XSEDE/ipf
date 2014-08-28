
###############################################################################
#   Copyright 2013 The University of Texas at Austin                          #
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

import json
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation

from glue2.entity import *

#######################################################################################################################

class Endpoint(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.URL = None                   # string (uri)
        self.Capability = []              # list of string (Capability)
        self.Technology = None            # string (EndpointTechnology)
        self.InterfaceName = "unknown"    # string (InterfaceName)
        self.InterfaceVersion = None      # string
        self.InterfaceExtension = []      # list of string (uri)
        self.WSDL = []                    # list of string (uri)
        self.SupportedProfile = []        # list of string (uri)
        self.Semantics = []               # list of string (uri)
        self.Implementor = None           # string
        self.ImplementationName = None    # string
        self.ImplementationVersion = None # string
        self.QualityLevel = "production"  # string (QualityLevel)
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
        self.ServiceID = None             # string (ID)
        self.ShareID = []                 # list of string (ID)
        self.AccessPolicyID = []          # list of string (ID)
        self.ActivityID = []              # list of string (ID)

#######################################################################################################################

class EndpointTeraGridXml(EntityTeraGridXml):
    data_cls = Endpoint

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Endpoint")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        if self.data.URL is not None:
            e = doc.createElement("URL")
            e.appendChild(doc.createTextNode(self.data.URL))
            element.appendChild(e)
        for capability in self.data.Capability:
            e = doc.createElement("Capability")
            e.appendChild(doc.createTextNode(capability))
            element.appendChild(e)
        if self.data.Technology is not None:
            e = doc.createElement("Technology")
            e.appendChild(doc.createTextNode(self.data.Technology))
            element.appendChild(e)
        if self.data.InterfaceName is not None:
            e = doc.createElement("InterfaceName")
            e.appendChild(doc.createTextNode(self.data.InterfaceName))
            element.appendChild(e)
        if self.data.InterfaceVersion is not None:
            e = doc.createElement("InterfaceVersion")
            e.appendChild(doc.createTextNode(self.data.InterfaceVersion))
            element.appendChild(e)
        for extension in self.data.InterfaceExtension:
            e = doc.createElement("InterfaceExtension")
            e.appendChild(doc.createTextNode(extension))
            element.appendChild(e)
        for wsdl in self.data.WSDL:
            e = doc.createElement("WSDL")
            e.appendChild(doc.createTextNode(wsdl))
            element.appendChild(e)
        for profile in self.data.SupportedProfile:
            e = doc.createElement("SupportedProfile")
            e.appendChild(doc.createTextNode(self.data.profile))
            element.appendChild(e)
        for semantics in self.data.Semantics:
            e = doc.createElement("Semantics")
            e.appendChild(doc.createTextNode(semantics))
            element.appendChild(e)
        if self.data.Implementor is not None:
            e = doc.createElement("Implementor")
            e.appendChild(doc.createTextNode(self.data.Implementor))
            element.appendChild(e)
        if self.data.ImplementationName is not None:
            e = doc.createElement("ImplementationName")
            e.appendChild(doc.createTextNode(self.data.ImplementationName))
            element.appendChild(e)
        if self.data.ImplementationVersion is not None:
            e = doc.createElement("ImplementationVersion")
            e.appendChild(doc.createTextNode(self.data.ImplementationVersion))
            element.appendChild(e)
        if self.data.QualityLevel is not None:
            e = doc.createElement("QualityLevel")
            e.appendChild(doc.createTextNode(self.data.QualityLevel))
            element.appendChild(e)
        if self.data.HealthState is not None:
            e = doc.createElement("HealthState")
            e.appendChild(doc.createTextNode(self.data.HealthState))
            element.appendChild(e)
        if self.data.HealthStateInfo is not None:
            e = doc.createElement("HealthStateInfo")
            e.appendChild(doc.createTextNode(self.data.HealthStateInfo))
            element.appendChild(e)
        if self.data.ServingState is not None:
            e = doc.createElement("ServingState")
            e.appendChild(doc.createTextNode(self.data.ServingState))
            element.appendChild(e)
        if self.data.StartTime is not None:
            e = doc.createElement("StartTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.StartTime)))
            element.appendChild(e)
        if self.data.IssuerCA is not None:
            e = doc.createElement("IssuerCA")
            e.appendChild(doc.createTextNode(self.data.IssuerCA))
            element.appendChild(e)
        for trustedCA in self.data.TrustedCA:
            e = doc.createElement("TrustedCA")
            e.appendChild(doc.createTextNode(trustedCA))
            element.appendChild(e)
        if self.data.DowntimeAnnounce is not None:
            e = doc.createElement("DowntimeAnnounce")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.DowntimeAnnounce)))
            element.appendChild(e)
        if self.data.DowntimeStart is not None:
            e = doc.createElement("DowntimeStart")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.DowntimeStart)))
            element.appendChild(e)
        if self.data.DowntimeEnd is not None:
            e = doc.createElement("DowntimeEnd")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.DowntimeEnd)))
            element.appendChild(e)
        if self.data.DowntimeInfo is not None:
            e = doc.createElement("DowntimeInfo")
            e.appendChild(doc.createTextNode(self.data.DowntimeInfo))
            element.appendChild(e)
        if self.data.ServiceID is not None:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(self.data.ServiceID))
            element.appendChild(e)
        for share in self.data.ShareID:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(share))
            element.appendChild(e)
        for activity in self.data.ActivityID:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(activity))
            element.appendChild(e)
    
#######################################################################################################################

class EndpointOgfJson(EntityOgfJson):
    data_cls = Endpoint

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.URL is not None:
            doc["URL"] = self.data.URL
        if len(self.data.Capability) > 0:
            doc["Capability"] = self.data.Capability
        if self.data.Technology is not None:
            doc["Technology"] = self.data.Technology
        doc["InterfaceName"] = self.data.InterfaceName
        if self.data.InterfaceVersion is not None:
            doc["InterfaceVersion"] = self.data.InterfaceVersion
        if len(self.data.InterfaceExtension) > 0:
            doc["InterfaceExtension"] = self.data.InterfaceExtension
        if len(self.data.WSDL) > 0:
            doc["WSDL"] = self.data.WSDL
        if len(self.data.SupportedProfile) > 0:
            doc["SupportedProfile"] = self.data.SupportedProfile
        if len(self.data.Semantics) > 0:
            doc["Semantics"] = self.data.Semantics
        if self.data.Implementor is not None:
            doc["Implementor"] = self.data.Implementor
        if self.data.ImplementationName is not None:
            doc["ImplementationName"] = self.data.ImplementationName
        if self.data.ImplementationVersion is not None:
            doc["ImplementationVersion"] = self.data.ImplementationVersion
        doc["QualityLevel"] = self.data.QualityLevel
        doc["HealthState"] = self.data.HealthState
        if self.data.HealthStateInfo is not None:
            doc["HealthStateInfo"] = self.data.HealthStateInfo
        doc["ServingState"] = self.data.ServingState
        if self.data.StartTime is not None:
            doc["StartTime"] = dateTimeToText(self.data.StartTime)
        if self.data.IssuerCA is not None:
            doc["IssuerCA"] = self.data.IssuerCA
        if len(self.data.TrustedCA) > 0:
            doc["TrustedCA"] = self.data.TrustedCA
        if self.data.DowntimeAnnounce is not None:
            doc["DowntimeAnnounce"] = dateTimeToText(self.data.DowntimeAnnounce)
        if self.data.DowntimeStart is not None:
            doc["DowntimeStart"] = dateTimeToText(self.data.DowntimeStart)
        if self.data.DowntimeEnd is not None:
            doc["DowntimeEnd"] = dateTimeToText(self.data.DowntimeEnd)
        if self.data.DowntimeInfo is not None:
            doc["DowntimeInfo"] = self.data.DowntimeInfo

        associations = {}
        associations["ServiceID"] = self.data.ServiceID
        associations["ShareID"] = self.data.ShareID
        if len(self.data.AccessPolicyID) > 0:
            associations["AccessPolicyID"] = self.data.AccesPolicyID
        if len(self.data.ActivityID) > 0:
            associations["ActivityID"] = self.data.ActivityID
        doc["Associations"] = associations

        return doc

#######################################################################################################################
