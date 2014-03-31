
###############################################################################
#   Copyright 2014 The University of Texas at Austin                          #
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

class Contact(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Detail = None   # A uri embedding the contact inforation
        self.Type = None     # ContactType_t
        self.ServiceID = []  # string uri
        self.DomainID = []   # string uri

#######################################################################################################################

class ContactOgfJson(EntityOgfJson):
    data_cls = Contact

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.Detail is not None:
            doc["Detail"] = self.data.Detail
        if self.data.Type is not None:
            doc["Type"] = self.data.Type
        if len(self.data.ServiceID) > 0:
            doc["ServiceID"] = self.data.ServiceID
        if len(self.data.DomainID) > 0:
            doc["DomainID"] = self.data.DomainID

        return doc

#######################################################################################################################
