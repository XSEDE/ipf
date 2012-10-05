
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
import os
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.name import SiteName
from ipf.step import Step

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

class Location(Data):

    DEFAULT_VALIDITY = 60*60*24 # seconds

    def __init__(self):
        Data.__init__(self)

        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = Location.DEFAULT_VALIDITY
        self.ID = None      # string (uri)
        self.Name = None    # string
        self.OtherInfo = [] # list of string
        self.Extension = {} # (key,value) strings

        # Location
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

class LocationIpfJson(Representation):
    data_cls = Location

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(location):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(location.CreationTime)
        if location.Validity is not None:
            doc["Validity"] = location.Validity
        doc["ID"] = location.ID
        if location.Name is not None:
            doc["Name"] = location.Name
        if len(location.OtherInfo) > 0:
            doc["OtherInfo"] = location.OtherInfo
        if len(location.Extension) > 0:
            doc["Extension"] = location.Extension

        # Location
        if location.Address is not None:
            doc["Address"] = location.Address
        if location.Place is not None:
            doc["Place"] = location.Place
        if location.Country is not None:
            doc["Country"] = location.Country
        if location.PostCode is not None:
            doc["PostCode"] = location.PostCode
        if location.Latitude is not None:
            doc["Latitude"] = location.Latitude
        if location.Longitude is not None:
            doc["Longitude"] = location.Longitude

        return doc
