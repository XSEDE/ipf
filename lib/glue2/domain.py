
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

class Domain(Entity):
    DEFAULT_VALIDITY = 60*60*24 # seconds

    def __init__(self):
        Entity.__init__(self)

        self.Description = None  # string
        self.WWW = None          # URL
        self.Contact = []        # Contact
        self.Location = None     # Location

#######################################################################################################################

class DomainOgfJson(EntityOgfJson):
    data_cls = Domain

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if domain.Description is not None:
            doc["Description"] = domain.Description
        if domain.WWW is not None:
            doc["WWW"] = domain.WWW
        if len(domain.Contact) > 0:
            doc["Contact"] = domain.Contact
        if domain.Location is not None:
            doc["Location"] = domain.Location

        return doc

#######################################################################################################################

class AdminDomain(Domain):
    def __init__(self):
        Domain.__init__(self)

        self.Distributed = None     # geographically-distributed resources (boolean)
        self.Owner = None           # person/entity that owns the resources (string)
        self.AdminDomain = []       # this domain aggregates others (id)
        self.ComputingService = []  # (id)
        self.StorageService = []    # (id)

#######################################################################################################################

class AdminDomainOgfJson(DomainOgfJson):
    data_cls = AdminDomain

    def __init__(self, data):
        DomainOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = DomainOgfJson.toJson(self)

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
