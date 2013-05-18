
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

class Service(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Capability = None   # string (Capability)
        self.Type = None         # string (ServiceType)
        self.QualityLevel = None # string (QualityLevel)
        self.StatusInfo = []     # list of string (uri)
        self.Complexity = None   # string
        self.Endpoint = []       # list of string (ID)
        self.Share = []          # list of string (ID)
        self.Manager = []        # list of string (ID)
        self.Contact = []        # list of string (ID)
        self.Location = None     # string (ID)
        self.Service = []        # list of string (ID)

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
        for endpoint in self.data.Endpoint:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            element.appendChild(e)
        for id in self.data.Share:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for id in self.data.Manager:
            e = doc.createElement("Manager")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for contact in self.data.Contact:
            e = doc.createElement("Contact")
            e.appendChild(doc.createTextNode(contact))
            element.appendChild(e)
        if self.data.Location is not None:
            e = doc.createElement("Location")
            e.appendChild(doc.createTextNode(self.data.Location))
            element.appendChild(e)
        for id in self.data.Service:
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
        if len(self.data.Endpoint) > 0:
            doc["Endpoint"] = self.data.Endpoint
        if len(self.data.Share) > 0:
            doc["Share"] = self.data.Share
        if len(self.data.Manager) > 0:
            doc["Manager"] = self.data.Manager
        if len(self.data.Contact) > 0:
            doc["Contact"] = self.data.Contact
        if self.data.Location is not None:
            doc["Location"] = self.data.Location
        if len(self.data.Service) > 0:
            doc["Service"] = self.data.Service

        return doc

#######################################################################################################################
