
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

class Resource(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.ManagerID = "urn:glue2:Manager:unknown"  # string (uri)
        self.ShareID = []                             # list of string (uri)
        self.ActivityID = []                          # list of string (uri)

#######################################################################################################################

class ResourceTeraGridXml(EntityTeraGridXml):
    data_cls = Resource

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Resource")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        if self.data.ManagerID is not None:
            e = doc.createElement("Manager")
            e.appendChild(doc.createTextNode(self.data.ManagerID))
            element.appendChild(e)
        for share in self.data.ShareID:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(share))
            element.appendChild(e)
        for activity in self.data.ActivityID:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(self.data.ActivityID))
            element.appendChild(e)
    
#######################################################################################################################

class ResourceOgfJson(EntityOgfJson):
    data_cls = Resource

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        associations = {}
        associations["ManagerID"] = self.data.ManagerID
        if len(self.data.ShareID) > 0:
            associations["ShareID"] = self.data.ShareID
        if len(self.data.ActivityID) > 0:
            associations["ActivityID"] = self.data.ActivityID
        doc["Associations"] = associations

        return doc

#######################################################################################################################
