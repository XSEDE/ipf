
###############################################################################
#   Copyright 2012-2013 The University of Texas at Austin                     #
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
import os
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.sysinfo import SiteName
from ipf.step import Step

from glue2.entity import *

#######################################################################################################################

class LocationStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "a geographical location"
        self._acceptParameter("location",
                              "A location as a dictionary. See Location.fromJson() for the keys and values.",
                              True)
        self.time_out = 5
        self.produces = [Location]

    def run(self):
        try:
            doc = self.params["location"]
        except KeyError:
            raise StepError("location not specified")
        location = Location()
        location.fromJson(doc)
        self._output(location)

#######################################################################################################################

class Location(Entity):

    DEFAULT_VALIDITY = 60*60*24 # seconds

    def __init__(self):
        Entity.__init__(self)

        self.Address = None    # street address (string)
        self.Place = None      # town/city (string)
        self.Country = None    # (string)
        self.PostCode = None   # postal code (string)
        self.Latitude = None   # degrees
        self.Longitude = None  # degrees

    def fromJson(self, doc):
        # Entity
        if "CreationTime" in doc:
            self.CreationTime = textToDateTime(doc["CreationTime"])
        else:
            self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = doc.get("Validity",Location.DEFAULT_VALIDITY)
        self.Name = doc.get("Name","unknown")
        self.ID = "urn:glue2:Location:%s" % self.Name.replace(" ","")
        self.id = self.ID
        self.OtherInfo = doc.get("OtherInfo",[])
        self.Extension = doc.get("Extension",{})

        self.Address = doc.get("Address")
        self.Place = doc.get("Place")
        self.Country = doc.get("Country")
        self.PostCode = doc.get("PostCode")
        self.Latitude = doc.get("Latitude")
        self.Longitude = doc.get("Longitude")

#######################################################################################################################

class LocationTeraGridXml(EntityTeraGridXml):
    data_cls = Location

    def __init__(self, data):
        EntityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("Location")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EntityTeraGridXml.addToDomElement(self,doc,element)

        if self.data.Address is not None:
            e = doc.createElement("Address")
            e.appendChild(doc.createTextNode(self.data.Address))
            element.appendChild(e)
        if self.data.Place is not None:
            e = doc.createElement("Place")
            e.appendChild(doc.createTextNode(self.data.Place))
            element.appendChild(e)
        if self.data.Country is not None:
            e = doc.createElement("Country")
            e.appendChild(doc.createTextNode(self.data.Country))
            element.appendChild(e)
        if self.data.PostCode is not None:
            e = doc.createElement("PostCode")
            e.appendChild(doc.createTextNode(self.data.PostCode))
            element.appendChild(e)
        if self.data.Latitude is not None:
            e = doc.createElement("Latitude")
            e.appendChild(doc.createTextNode(str(self.data.Latitude)))
            element.appendChild(e)
        if self.data.Longitude is not None:
            e = doc.createElement("Longitude")
            e.appendChild(doc.createTextNode(str(self.data.Longitude)))
            element.appendChild(e)

#######################################################################################################################

class LocationOgfJson(EntityOgfJson):
    data_cls = Location

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.Address is not None:
            doc["Address"] = self.data.Address
        if self.data.Place is not None:
            doc["Place"] = self.data.Place
        if self.data.Country is not None:
            doc["Country"] = self.data.Country
        if self.data.PostCode is not None:
            doc["PostCode"] = self.data.PostCode
        if self.data.Latitude is not None:
            doc["Latitude"] = self.data.Latitude
        if self.data.Longitude is not None:
            doc["Longitude"] = self.data.Longitude

        return doc

#######################################################################################################################
