
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

class Benchmark(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Type = None                # Benchmark_t
        self.Value = None               # a number
        self.ComputingManagerID = None  # string uri

#######################################################################################################################

class BenchmarkOgfJson(EntityOgfJson):
    data_cls = Benchmark

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.Type is not None:
            doc["Type"] = self.data.Type
        if self.data.Value is not None:
            doc["Value"] = self.data.Value
        if self.data.ComputingManagerID is not None:
            doc["ComputingManagerID"] = self.data.ComputingManagerID

        return doc

#######################################################################################################################
