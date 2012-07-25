
###############################################################################
#   Copyright 2011 The University of Texas at Austin                          #
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

import commands
import os
import re
import sys

from glue2.computing_endpoint import *

#######################################################################################################################

class GenesisEndpointStep(ParamComputingEndpointStep):
    def __init__(self, params):
        ParamComputingEndpointStep.__init__(self,params)
        self.name = "glue2/genesisII/computing_endpoint"
        self.description = "create a ComputingEndpoint for Genesis II using parameters"

    def _run(self):
        endpoints = ParamComputingEndpointStep._run(self)
        for endpoint in endpoints:
            endpoint.Capability = ["executionmanagement.jobdescription",
                                   "executionmanagement.jobexecution",
                                   "executionmanagement.jobmanager",
                                   ]
            endpoint.Implementor = "University of Virginia"
            endpoint.ImplementationName = "Genesis II"
            endpoint.Technology = "webservice"
            endpoint.InterfaceName = "ogf.bes"
        return endpoints

#######################################################################################################################