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
import copy
import os
import re
import sys

from glue2.computing_endpoint import *

#######################################################################################################################

class GramEndpointsStep(ComputingEndpointsStep):

    name = "glue2/teragrid/gram_endpoints"
    description = "create ComputingEndpoints for GRAM by examining the local TeraGrid registration information"
    accepts_params = copy.copy(ComputingEndpointsStep.accepts_params)
    accepts_params["core_kit_directory"] = "the path to the TeraGrid core kit installation"
    accepts_params["ca_certificates_directory"] = "the path to the CA directory (default /etc/grid-security/certificates"
    accepts_params["host_certificate"] = "the path to the host certificate file (default /etc/grid-security/hostcert.pem)"
    accepts_params["container_certificate"] = "the path to the GRAM 4 container certificate file (default /etc/grid-security/containercert.pem)"
    accepts_params["grid-cert-info"] = "the path to the 'grid-cert-info' command (default 'grid-cert-info')"

    def __init__(self, params):
        ComputingEndpointsStep.__init__(self,params)

    def _run(self):
        try:
            corekit_dir = self.params["core_kit_directory"]
        except KeyError:
            self.error("core_kit_directory not specified")
            sys.exit(1)
        
        kits_file = os.path.join(corekit_dir,"etc","registeredkits.conf")
        try:
            kit_dirs = self._readRegisteredKits(kits_file)
        except:
            self.error("failed to read registered kits file "+kits_file)
            sys.exit(1)

        service_dir = None
        kit_conf_file = None
        for kit_dir in kit_dirs:
            if kit_dir.find("ctss-remote-compute") >= 0:
                service_dir = os.path.join(kit_dir,"reg","service")
                kit_conf_file = os.path.join(kit_dir,"reg","kit.conf")
                break
        if service_dir == None:
            self.error("CTSS remote compute kit not found in registered kits file "+kitsFile)
            sys.exit(1)

        support_level = None
        file = open(kit_conf_file,"r")
        for line in file:
            if line.find("#") != -1:
                line = line[:line.find("#")]
            m = re.search("\s*SupportLevel\s*=\s*(\S+)",line)
            if m == None:
                continue
            if m.group(1) == None:
                continue
            support_level = m.group(1)
            break
        file.close()

        endpoints = []
        entries = os.listdir(service_dir)
        for entry in entries:
            if entry.endswith(".conf"):
                if entry.find("gram") != -1:
                    file_name = os.path.join(service_dir,entry)
                    try:
                        reg_info = self._readKitRegistration(file_name)
                    except:
                        self.warning("failed to read kit conf file "+file_name)
                        continue
                    endpoints.append(self._createEndpoint(reg_info,support_level))

        return endpoints

    def _readRegisteredKits(self, file):
        file = open(file,"r")
        lines = file.readlines()
        file.close()
        kitDirs = []
        for line in lines:
            if line.startswith("#"):
                continue
            toks = line.split("= ")
            if len(toks) != 2:
                continue
            name = toks[0].lstrip().rstrip()
            value = toks[1].lstrip().rstrip()
            if name == "kit":
                kitDirs.append(value)
        return kitDirs

    def _readKitRegistration(self, file):
        """Reads a .conf file into a hash."""
        file = open(file,"r")
        lines = file.readlines()
        file.close()
        info = {}
        for line in lines:
            if line.startswith("#"):
                continue
            toks = line.split("=")
            if len(toks) != 2:
                continue
            name = toks[0].lstrip().rstrip()
            value = toks[1].lstrip().rstrip()
            info[name] = value
        return info

    def _createEndpoint(self, reg_info, quality_level):
        endpoint = GramEndpoint()

        ca_dir = "/etc/grid-security/certificates"
        try:
            ca_dir = self.params["ca_certificates_directory"]
        except KeyError:
            pass
        # this is slow - about 1 second per CA file. and there are lots of CA files
        #endpoint.TrustedCA = self._getSubjects(ca_dir)

        endpoint.Name = reg_info["Name"]
        endpoint.ID = "http://"+self.resource_name+"/glue2/ComputingEndpoint/"+endpoint.Name
        endpoint.URL = reg_info["Endpoint"]

        endpoint.ComputingService = "http://"+self.resource_name+"/glue2/ComputingService"

        host_cert_file = "/etc/grid-security/hostcert.pem"
        try:
            host_cert_file = self.params["host_certificate"]
        except KeyError:
            pass
        container_cert_file = "/etc/grid-security/containercert.pem"
        try:
            container_cert_file = self.params["container_certificate"]
        except KeyError:
            pass

        if reg_info["Type"] == "prews-gram":
            endpoint.Technology = "legacy"
            endpoint.InterfaceName = "globus.prews-gram"
            endpoint.IssuerCA = self._getIssuer(host_cert_file)
        elif reg_info["Type"] == "ws-gram":
            endpoint.Technology = "webservice"
            endpoint.InterfaceName = "globus.ws-gram"
            endpoint.IssuerCA = self._getIssuer(container_cert_file)
            #self.WSDL
        elif reg_info["Type"] == "gram5":
            endpoint.Technology = "legacy"
            endpoint.InterfaceName = "globus.gram5"
            endpoint.IssuerCA = self._getIssuer(host_cert_file)
        endpoint.ImplementationName = reg_info["Type"]
        endpoint.ImplementationVersion = reg_info["Version"]

        endpoint.QualityLevel = quality_level

        return endpoint

    def _getIssuer(self, caFile):
        grid_cert_info = "grid-cert-info"
        try:
            grid_cert_info = self.params["grid-cert-info"]
        except KeyError:
            pass
        
        cmd = grid_cert_info + " -issuer -file "+caFile
        (status, output) = commands.getstatusoutput(cmd)
        if status == 0:
            return output
        else:
            self.warning("getIssuer failed on grid-cert-info: "+output)
            return None

    def _getSubjects(self, caDir):
        subjects = []
        entries = os.listdir(caDir)
        for entry in entries:
            if entry.endswith(".0"):
                subject = self._getSubject(os.path.join(caDir,entry))
                if subject != None:
                    subjects.append(subject)
        return subjects

    def _getSubject(self, caFile):
        grid_cert_info = "grid-cert-info"
        try:
            grid_cert_info = self.params["grid-cert-info"]
        except KeyError:
            pass

        cmd = grid_cert_info + " -subject -file "+caFile
        status, output = commands.getstatusoutput(cmd)
        if status == 0:
            return output
        else:
            self.warning("getSubject failed on grid-cert-info: "+output)
            return None

##############################################################################################################

class GramEndpoint(ComputingEndpoint):
    def __init__(self):
        ComputingEndpoint.__init__(self)

        self.Capability = ["executionmanagement.jobdescription",
                           "executionmanagement.jobexecution",
                           "executionmanagement.jobmanager",
                           ]
        self.Implementor = "The Globus Alliance"

##############################################################################################################
