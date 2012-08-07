#!/usr/bin/env python

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
import socket
import sys

from glue2.computing_endpoint import *

#######################################################################################################################

class NimbusEndpointStep(ComputingEndpointStep):
    def __init__(self):
        ComputingEndpointStep.__init__(self)

        self.description = "create ComputingEndpoints for Nimbus"
        self._acceptParameter("host_name",
                              "the name of the host the Nimbus service runs on (default is the local host)",
                              False)
        self._acceptParameter("nimbus_version","the version of Nimbus installed (optional)",False)
        self._acceptParameter("nimbus_dir","the path to the nimbus directory (optional)",False)

    def _run(self):
        try:
            host_name = self.params["host_name"]
        except KeyError:
            host_name = socket.getfqdn()

        issuer = self._getIssuer()

        endpoints = []

        endpoint = self._getEndpoint(issuer)
        endpoint.Name = "wsrf"
        endpoint.URL = "http://%s:8443" % host_name
        endpoint.Technology = "SOAP"
        endpoint.InterfaceName = "WSRF"
        endpoints.append(endpoint)

        endpoint = self._getEndpoint(issuer)
        endpoint.Name = "rest"
        endpoint.URL = "http://%s:8444" % host_name
        endpoint.Technology = "REST"
        endpoint.InterfaceName = "EC2"
        endpoints.append(endpoint)

        return endpoints

    def _getEndpoint(self, issuer):
        endpoint = ComputingEndpoint()
        endpoint.Capability = ["executionmanagement.jobdescription",
                           "executionmanagement.jobexecution",
                           "executionmanagement.jobmanager",
                           ]
        endpoint.Implementor = "The Nimbus Project"
        endpoint.ImplementationName = "Nimbus"
        try:
            endpoint.ImplementationVersion = self.params["nimbus_version"]
        except KeyError:
            pass
        endpoint.QualityLevel = "production"
        endpoint.IssuerCA = issuer

        return endpoint

    def _getIssuer(self):
        try:
            nimbus_dir = self.params["nimbus_dir"]
        except KeyError:
            return None

        cert_file = os.path.join(nimbus_dir,"var","hostcert.pem")
        grid_cert_info = os.path.join(nimbus_dir,"services","bin","grid-cert-info")

        os.environ["GLOBUS_LOCATION"] = os.path.join(nimbus_dir,"services")
        cmd = grid_cert_info + " -issuer -file "+cert_file
        (status, output) = commands.getstatusoutput(cmd)
        if status == 0:
            try:
                # remove the 'issuer      : ' prefix and strip off any leading and trailing whitespace
                return output[output.index(":")+1:].strip()
            except ValueError:
                self.warning("getIssuer failed to process output of grid-cert-info: %s",output)
                return None
        else:
            self.warning("getIssuer failed on grid-cert-info: %s",output)
            return None

#######################################################################################################################
