
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
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *

#######################################################################################################################

class Entity(Data):
    def __init__(self):
        Data.__init__(self)

        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = None
        self.ID = "urn:glue2:Unknown:unknown"   # string (uri)
        self.Name = None                        # string
        self.OtherInfo = []                     # list of string
        self.Extension = {}                     # (key,value) strings

#######################################################################################################################

class EntityTeraGridXml(Representation):
    data_cls = Entity

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    # Entity is abstract, so don't implement get()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Entity")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        element.setAttribute("CreationTime",dateTimeToText(self.data.CreationTime))
        if self.data.Validity is not None:
            element.setAttribute("Validity",str(self.data.Validity))

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(self.data.ID))
        element.appendChild(e)

        if self.data.Name is not None:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(self.data.Name))
            element.appendChild(e)
        for info in self.data.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            element.appendChild(e)
        for key in self.data.Extension.keys():
            e = doc.createElement("Extension")
            e.setAttribute("Key",key)
            e.appendChild(doc.createTextNode(str(self.data.Extension[key])))
            element.appendChild(e)

#######################################################################################################################

class EntityOgfJson(Representation):
    data_cls = Entity

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    # Entity is abstract, so don't implement get()

    def toJson(self):
        doc = {}
        
        doc["CreationTime"] = dateTimeToText(self.data.CreationTime)
        if self.data.Validity is not None:
            doc["Validity"] = self.data.Validity
        doc["ID"] = self.data.ID
        if self.data.Name is not None:
            doc["Name"] = self.data.Name
        if len(self.data.OtherInfo) > 0:
            doc["OtherInfo"] = self.data.OtherInfo
        if len(self.data.Extension) > 0:
            doc["Extension"] = {}
            for name in self.data.Extension:
                if isinstance(self.data.Extension[name],datetime.datetime):
                    doc["Extension"][name] = dateTimeToText(self.data.Extension[name])
                else:
                    doc["Extension"][name] = self.data.Extension[name]

        return doc

#######################################################################################################################
