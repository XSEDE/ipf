
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

from .entity import *

#######################################################################################################################

class Activity(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.UserDomainID = None # string uri
        self.EndpointID = None   # string uri
        self.ShareID = None      # string uri
        self.ResourceID = None   # string uri
        self.EnvironmentID = None   # string uri
        self.ActivityID = []     # list of string uri

#######################################################################################################################

class ActivityTeraGridXml(EntityTeraGridXml):
    data_cls = Activity

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Activity")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        if self.data.UserDomainID is not None:
            e = doc.createElement("UserDomain")
            e.appendChild(doc.createTextNode(self.data.UserDomainID))
            element.appendChild(e)
        if self.data.EndpointID is not None:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(self.data.EndpointID))
            element.appendChild(e)
        if self.data.ShareID is not None:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(self.data.ShareID))
            element.appendChild(e)
        if self.data.ResourceID is not None:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(self.data.ResourceID))
            element.appendChild(e)
        if self.data.EnvironmentID is not None:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(self.data.EnvironmentID))
            element.appendChild(e)
        for act in self.data.ActivityID:
            e = doc.createElement("Activity")
            e.appendChild(doc.createTextNode(act))
            element.appendChild(e)
    
#######################################################################################################################

class ActivityOgfJson(EntityOgfJson):
    data_cls = Activity

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        associations = {}
        associations["UserDomainID"] = self.data.UserDomainID
        associations["EndpointID"] = self.data.EndpointID
        associations["ShareID"] = self.data.ShareID
        associations["ResourceID"] = self.data.ResourceID
        associations["EnvironmentID"] = self.data.EnvironmentID
        associations["ActivityID"] = self.data.ActivityID

        doc["Associations"] = associations

        return doc

#######################################################################################################################
