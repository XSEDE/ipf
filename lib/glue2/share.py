
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

class Share(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Description = None  # string
        self.Endpoint = []       # list of string (uri)
        self.Resource = []       # list of string (uri)
        self.Service = None      # string (uri)
        self.Activity = []       # list of string (uri)
        self.MappingPolicy = []  # list of string (uri)

#######################################################################################################################

class ShareTeraGridXml(EntityTeraGridXml):
    data_cls = Share

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)

        root = doc.createElement("Share")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        if self.data.Description is not None:
            e = doc.createElement("Description")
            e.appendChild(doc.createTextNode(self.data.Description))
            element.appendChild(e)
        for endpoint in self.data.Endpoint:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(endpoint))
            element.appendChild(e)
        for resource in self.data.Resource:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(resource))
            element.appendChild(e)
        if self.data.Service is not None:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(self.data.Service))
            element.appendChild(e)
        for activity in self.data.Activity:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(activity))
            element.appendChild(e)
        for policy in self.data.MappingPolicy:
            e = doc.createElement("MappingPolicy")
            e.appendChild(doc.createTextNode(policy))
            element.appendChild(e)
    
#######################################################################################################################

class ShareOgfJson(EntityOgfJson):
    data_cls = Share

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.Description is not None:
            doc["Description"] = self.data.Description
        if len(self.data.Endpoint) > 0:
            doc["Endpoint"] = self.data.Endpoint
        if len(self.data.Resource) > 0:
            doc["Resource"] = self.data.Resource
        if self.data.Service is not None:
            doc["Service"] = self.data.Service
        if len(self.data.Activity) > 0:
            doc["Activity"] = self.data.Activity
        if len(self.data.MappingPolicy) > 0:
            doc["MappingPolicy"] = self.data.MappingPolicy

        return doc

#######################################################################################################################
