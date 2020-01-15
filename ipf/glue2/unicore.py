
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

import subprocess
import os
import re
import sys

import ipf.glue2.computing_endpoint

#######################################################################################################################

class EndpointStep(ipf.glue2.computing_endpoint.ParamComputingEndpointStep):
    def __init__(self):
        ipf.glue2.computing_endpoint.ParamComputingEndpointStep.__init__(self)
        self.description = "create a ComputingEndpoint for Unicore using parameters"

    def _run(self):
        endpoints = ipf.glue2.computing_endpoint.ParamComputingEndpointStep._run(self)
        for endpoint in endpoints:
            endpoint.Capability = ["executionmanagement.jobdescription",
                                   "executionmanagement.jobexecution",
                                   "executionmanagement.jobmanager",
                                   ]
            endpoint.Implementor = "Julich Supercomputing Center"
            endpoint.ImplementationName = "Unicore"
            endpoint.Technology = "webservice"
            endpoint.InterfaceName = "ogf.bes"
            endpoint.JobDescription = ["ogf.jsdl:1.0"]
        return endpoints

#######################################################################################################################
