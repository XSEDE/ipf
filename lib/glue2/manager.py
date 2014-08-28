
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

class Manager(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.ProductName = "unknown"                  # string
        self.ProductVersion = None                    # string
        self.ServiceID = "urn:glue2:Service:unknown"  # string (ID)
        self.ResourceID = []                          # list of string (ID)

#######################################################################################################################

class ManagerTeraGridXml(EntityTeraGridXml):
    data_cls = Manager

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Manager")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        if self.data.ProductName != None:
            e = doc.createElement("ProductName")
            e.appendChild(doc.createTextNode(self.data.ProductName))
            element.appendChild(e)
        if self.data.ProductVersion != None:
            e = doc.createElement("ProductVersion")
            e.appendChild(doc.createTextNode(self.data.ProductVersion))
            element.appendChild(e)
        if self.data.ServiceID is not None:
            e = doc.createElement("Service")
            e.appendChild(doc.createTextNode(self.data.ServiceID))
            element.appendChild(e)
        for resource in self.data.ResourceID:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(resource))
            element.appendChild(e)

#######################################################################################################################

class ManagerOgfJson(EntityOgfJson):
    data_cls = Manager

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        doc["ProductName"] = self.data.ProductName
        if self.data.ProductVersion != None:
            doc["ProductVersion"] = self.data.ProductVersion

        associations = {}
        associations["ServiceID"] = self.data.ServiceID
        associations["ResourceID"] = self.data.ResourceID
        doc["Associations"] = associations

        return doc

#######################################################################################################################
