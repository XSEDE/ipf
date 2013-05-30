
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

class Resource(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Manager = None # string (uri)
        self.Share = []     # list of string (uri)
        self.Activity = []  # list of string (uri)

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

        if self.data.Manager is not None:
            e = doc.createElement("Manager")
            e.appendChild(doc.createTextNode(self.data.Manager))
            element.appendChild(e)
        for share in self.data.Share:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(share))
            element.appendChild(e)
        for activity in self.data.Activity:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(self.data.Activity))
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

        if self.data.Manager is not None:
            doc["Manager"] = self.data.Manager
        if len(self.data.Share) > 0:
            doc["Share"] = self.data.Share
        if len(self.data.Activity) > 0:
            doc["Activity"] = self.data.Activity

        return doc

#######################################################################################################################
