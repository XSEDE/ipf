
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

class AdminDomainStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "a domain containing a number of services"
        self._acceptParameter("admin_domain",
                              "An AdminDomain as a dictionary. See AdminDomain.fromJson() for the keys and values.",
                              True)
        self.time_out = 5
        self.produces = [AdminDomain]

    def run(self):
        try:
            doc = self.params["admin_domain"]
        except KeyError:
            raise StepError("admin_domain not specified")
        domain = AdminDomain()
        domain.fromJson(doc)
        self._output(domain)

#######################################################################################################################

class Domain(Data):

    DEFAULT_VALIDITY = 60*60*24 # seconds

    def __init__(self):
        Data.__init__(self)

        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = Domain.DEFAULT_VALIDITY
        self.ID = None      # string (uri)
        self.Name = None    # string
        self.OtherInfo = [] # list of string
        self.Extension = {} # (key,value) strings

        # Domain
        self.Description = None  # string
        self.WWW = None          # URL
        self.Contact = []        # Contact
        self.Location = None     # Location

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

        self.Description = doc.get("Description")
        self.WWW = doc.get("WWW")
        self.Contact = doc.get("Contact",[])
        self.Location = doc.get("Location")

#######################################################################################################################

class AdminDomain(Domain):
    def __init__(self):
        Domain.__init__(self)

        # AdminDomain
        self.Distributed = None     # geographically-distributed resources (boolean)
        self.Owner = None           # person/entity that owns the resources (string)
        self.AdminDomain = []       # this domain aggregates others (id)
        self.ComputingService = []  # (id)
        self.StorageService = []    # (id)

    def fromJson(self, doc):
        Domain.fromJson(self,doc)
        self.Distributed = doc.get("Distributed")
        self.Owner = doc.get("Owner")
        self.AdminDomain = doc.get("AdminDomain")
        self.ComputingService = doc.get("ComputingService")
        self.StorageService = doc.get("StorageService")

#######################################################################################################################

class AdminDomainIpfJson(Representation):
    data_cls = AdminDomain

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(domain):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(domain.CreationTime)
        if domain.Validity is not None:
            doc["Validity"] = domain.Validity
        doc["ID"] = domain.ID
        if domain.Name is not None:
            doc["Name"] = domain.Name
        if len(domain.OtherInfo) > 0:
            doc["OtherInfo"] = domain.OtherInfo
        if len(domain.Extension) > 0:
            doc["Extension"] = domain.Extension

        # Domain
        if domain.Description is not None:
            doc["Description"] = domain.Description
        if domain.WWW is not None:
            doc["WWW"] = domain.WWW
        if len(domain.Contact) > 0:
            doc["Contact"] = domain.Contact
        if domain.Location is not None:
            doc["Location"] = domain.Location

        # AdminDomain
        if domain.Distributed is not None:
            doc["Distributed"] = domain.Distributed
        if domain.Owner is not None:
            doc["Owner"] = domain.Owner
        if len(domain.AdminDomain) > 0:
            doc["AdminDomain"] = domain.AdminDomain
        if len(domain.ComputingService) > 0:
            doc["ComputingService"] = domain.ComputingService
        if len(domain.StorageService) > 0:
            doc["StorageService"] = domain.StorageService

        return doc

#######################################################################################################################
