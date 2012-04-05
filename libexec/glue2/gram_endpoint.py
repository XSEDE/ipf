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
import ConfigParser

from ipf.error import *
from ipf.step import Step, StepEngine
from teragrid.glue2.computing_endpoint import *

#######################################################################################################################

class GramEndpointsStep(ComputingEndpointsStep):
    def __init__(self, params={}):
        ComputingEndpointsStep.__init__(self,params)

        self.name = "glue2/teragrid/gram_endpoints"

    def _run(self):
        try:
            corekit_dir = self.engine.config.get("teragrid","core_kit_directory")
        except ConfigParser.Error:
            raise StepError("teragrid.core_kit_directory not specified")
        
        kits_file = os.path.join(corekit_dir,"etc","registeredkits.conf")
        try:
            kit_dirs = self._readRegisteredKits(kits_file)
        except:
            raise StepError("failed to read registered kits file "+kits_file)

        service_dir = None
        kit_conf_file = None
        for kit_dir in kit_dirs:
            if kit_dir.find("ctss-remote-compute") >= 0:
                service_dir = os.path.join(kit_dir,"reg","service")
                kit_conf_file = os.path.join(kit_dir,"reg","kit.conf")
                break
        if service_dir == None:
            raise StepError("CTSS remote compute kit not found in registered kits file "+kitsFile)

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
                        self.warn("failed to read kit conf file "+file_name)
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
            ca_dir = self.engine.config.get("globus","ca_certificates_directory")
        except ConfigParser.Error:
            pass
        # this is slow - about 1 second per CA file. and there are lots of CA files
        #endpoint.TrustedCA = self._getSubjects(ca_dir)

        endpoint.Name = reg_info["Name"]
        endpoint.ID = "http://"+self.resource_name+"/glue2/ComputingEndpoint/"+endpoint.Name
        endpoint.URL = reg_info["Endpoint"]

        endpoint.ComputingService = "http://"+self.resource_name+"/glue2/ComputingService"

        host_cert_file = "/etc/grid-security/hostcert.pem"
        try:
            host_cert_file = self.engine.config.get("globus","host_certificate")
        except ConfigParser.Error:
            pass
        container_cert_file = "/etc/grid-security/containercert.pem"
        try:
            container_cert_file = self.engine.config.get("globus","container_certificate")
        except ConfigParser.Error:
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
            grid_cert_info = self.engine.config.get("globus","grid-cert-info")
        except ConfigParser.Error:
            pass
        
        cmd = grid_cert_info + " -issuer -file "+caFile
        (status, output) = commands.getstatusoutput(cmd)
        if status == 0:
            return output
        else:
            logger.warning("getIssuer failed on grid-cert-info: "+output)
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
            grid_cert_info = self.engine.config.get("globus","grid-cert-info")
        except ConfigParser.Error:
            pass

        cmd = grid_cert_info + " -subject -file "+caFile
        status, output = commands.getstatusoutput(cmd)
        if status == 0:
            return output
        else:
            logger.warning("getSubject failed on grid-cert-info: "+output)
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

if __name__ == "__main__":
    StepEngine(GramEndpointsStep())
