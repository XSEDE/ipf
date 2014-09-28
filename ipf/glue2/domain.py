
###############################################################################
#   Copyright 2012-2014 The University of Texas at Austin                     #
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

from .entity import *

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
        self.ContactID = []        # Contact
        self.LocationID = None     # Location

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

        associations = {}
        if len(domain.ContactID) > 0:
            associations["ContactID"] = domain.ContactID
        associations["LocationID"] = domain.LocationID
        doc["Associations"] = associations

        return doc

#######################################################################################################################

class AdminDomain(Domain):
    def __init__(self):
        Domain.__init__(self)

        self.Distributed = None       # geographically-distributed resources (boolean)
        self.Owner = None             # person/entity that owns the resources (string)
        self.ServiceID = []           # services managed by this domain (id)
        self.ChildDomainID = []       # this domain aggregates others (id)
        self.ParentDomainID = None    # this domain is part of another
        self.ComputingServiceID = []  # (id)
        self.StorageServiceID = []    # (id)

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

        associations = {}
        if len(domain.ServiceID) > 0:
            associations["ServiceID"] = domain.ServiceID
        if len(domain.ChildDomainID) > 0:
            associations["ChildDomainID"] = domain.ChildDomainID
        associations["ParentDomainID"] = domain.ParentDomainID
        if len(domain.ComputingServiceID) > 0:
            associations["ComputingServiceID"] = domain.ComputingServiceID
        if len(domain.StorageServiceID) > 0:
            associations["StorageServiceID"] = domain.StorageServiceID
        doc["Associations"] = associations

        return doc

#######################################################################################################################
