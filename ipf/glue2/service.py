
###############################################################################
#   Copyright 2013-2014 The University of Texas at Austin                     #
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

from .entity import *

#######################################################################################################################

class Service(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Capability = None                          # string (Capability)
        self.Type = None                                # string (ServiceType)
        self.QualityLevel = None                        # string (QualityLevel)
        self.StatusInfo = []                            # list of string (uri)
        self.Complexity = None                          # string
        self.EndpointID = []                            # list of string (ID)
        self.ShareID = []                               # list of string (ID)
        self.ManagerID = []                             # list of string (ID)
        self.ContactID = []                             # list of string (ID)
        self.LocationID = "urn:ogf:glue2:xsede.org:Location:unknown"  # string (ID)
        self.ServiceID = []                             # list of string (ID)

#######################################################################################################################

class ServiceTeraGridXml(EntityTeraGridXml):
    data_cls = Service

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Service")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        for capability in self.data.Capability:
            e = doc.createElement("Capability")
            e.appendChild(doc.createTextNode(capability))
            element.appendChild(e)
        if self.data.Type is not None:
            e = doc.createElement("Type")
            e.appendChild(doc.createTextNode(self.data.Type))
            element.appendChild(e)
        if self.data.QualityLevel is not None:
            e = doc.createElement("QualityLevel")
            e.appendChild(doc.createTextNode(self.data.QualityLevel))
            element.appendChild(e)
        for status in self.data.StatusInfo:
            e = doc.createElement("StatusInfo")
            e.appendChild(doc.createTextNode(status))
            element.appendChild(e)
        if self.data.Complexity is not None:
            e = doc.createElement("Complexity")
            e.appendChild(doc.createTextNode(self.data.Complexity))
            element.appendChild(e)
        for endpoint in self.data.EndpointID:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            element.appendChild(e)
        for id in self.data.ShareID:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for id in self.data.ManagerID:
            e = doc.createElement("Manager")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for contact in self.data.ContactID:
            e = doc.createElement("Contact")
            e.appendChild(doc.createTextNode(contact))
            element.appendChild(e)
        if self.data.LocationID is not None:
            e = doc.createElement("Location")
            e.appendChild(doc.createTextNode(self.data.LocationID))
            element.appendChild(e)
        for id in self.data.ServiceID:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
    
#######################################################################################################################

class ServiceOgfJson(EntityOgfJson):
    data_cls = Service

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        # Service
        if len(self.data.Capability) > 0:
            doc["Capability"] = self.data.Capability
        if self.data.Type is not None:
            doc["Type"] = self.data.Type
        if self.data.QualityLevel is not None:
            doc["QualityLevel"] = self.data.QualityLevel
        if len(self.data.StatusInfo) > 0:
            doc["StatusInfo"] = self.data.StatusInfo
        if self.data.Complexity is not None:
            doc["Complexity"] = self.data.Complexity

        associations = {}
        if len(self.data.EndpointID) > 0:
            associations["EndpointID"] = self.data.EndpointID
        if len(self.data.ShareID) > 0:
            associations["ShareID"] = self.data.ShareID
        if len(self.data.ManagerID) > 0:
            associations["ManagerID"] = self.data.ManagerID
        associations["ContactID"] = self.data.ContactID
        associations["LocationID"] = self.data.LocationID
        associations["ServiceID"] = self.data.ServiceID
        doc["Associations"] = associations

        return doc

#######################################################################################################################
