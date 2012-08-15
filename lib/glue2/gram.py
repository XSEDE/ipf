
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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

import glue2.computing_endpoint

#######################################################################################################################

class EndpointStep(glue2.computing_endpoint.ParamComputingEndpointStep):
    def __init__(self):
        glue2.computing_endpoint.ParamComputingEndpointStep.__init__(self)
        self.description = "create a ComputingEndpoint for GRAM using parameters"

    def _run(self):
        endpoints = glue2.computing_endpoint.ParamComputingEndpointStep._run(self)
        for endpoint in endpoints:
            endpoint.Capability = ["executionmanagement.jobdescription",
                                   "executionmanagement.jobexecution",
                                   "executionmanagement.jobmanager",
                                   ]
            endpoint.Implementor = "The Globus Alliance"
            endpoint.ImplementationName = "GRAM"
        return endpoints

#######################################################################################################################

class Version2EndpointStep(EndpointStep):
    def __init__(self):
        EndpointStep.__init__(self)
        self.description = "create a ComputingEndpoint for GRAM2 using parameters"

    def _run(self):
        endpoints = EndpointStep._run(self)
        for endpoint in endpoints:
            endpoint.Technology = "legacy"
            endpoint.InterfaceName = "globus.prews-gram"
            if endpoint.ImplementationVersion == None:
                endpoint.ImplementationVersion = "2"
            endpoint.JobDescription = ["globus.rsl"]
        return endpoints

#######################################################################################################################

class Version4EndpointStep(EndpointStep):
    def __init__(self):
        EndpointStep.__init__(self)
        self.description = "create a ComputingEndpoint for GRAM4 (WS-GRAM) using parameters"

    def _run(self):
        endpoints = EndpointStep._run(self)
        for endpoint in endpoints:
            endpoint.Technology = "webservice"
            endpoint.InterfaceName = "globus.ws-gram"
            if endpoint.ImplementationVersion == None:
                endpoint.ImplementationVersion = "4"
            endpoint.JobDescription = ["globus.rsl"]
        return endpoints

#######################################################################################################################

class Version5EndpointStep(EndpointStep):
    def __init__(self):
        EndpointStep.__init__(self)
        self.description = "create a ComputingEndpoint for GRAM5 using parameters"

    def _run(self):
        endpoints = EndpointStep._run(self)
        for endpoint in endpoints:
            endpoint.Technology = "legacy"
            endpoint.InterfaceName = "globus.gram5"
            if endpoint.ImplementationVersion == None:
                endpoint.ImplementationVersion = "5"
            endpoint.JobDescription = ["globus.rsl"]
        return endpoints

#######################################################################################################################
