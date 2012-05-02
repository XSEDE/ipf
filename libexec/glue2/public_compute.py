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

import os
import ConfigParser

from ipf.engine import StepEngine
from ipf.error import StepError
from ipf.step import Step

#######################################################################################################################

class PublicComputeStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "glue2/teragrid/public_compute"
        self.description = "creates a single document containing all nonsensitive compute-related information"
        self.time_out = 5
        self.requires_types = ["ipf/resource_name.txt",
                               "ipf/site_name.txt",
                               "glue2/teragrid/computing_service.json",
                               "glue2/teragrid/computing_endpoints.json",
                               "glue2/teragrid/computing_shares.json",
                               "glue2/teragrid/computing_manager.json",
                               "glue2/teragrid/execution_environments.json",]
        self.produces_types = ["glue2/teragrid/public_compute.xml",
                               "glue2/teragrid/public_compute.json"]

        self.more_inputs = True

        self.public_compute = PublicCompute()

    def input(self, document):
        if document.type == "ipf/resource_name.txt":
            self.public_compute.resource_name = document.body.rstrip()
        elif document.type == "ipf/site_name.txt":
            self.public_compute.site_name = document.body.rstrip()
        elif document.type == "glue2/teragrid/computing_service.json":
            try:
                self.public_compute.service = document.service
            except AttributeError:
                self.public_compute.service = self._parseServiceJson(document.body)
        elif document.type == "glue2/teragrid/computing_endpoints.json":
            try:
                self.public_compute.endpoints = document.endpoints
            except AttributeError:
                self.public_compute.endpoints = self._parseEndpointsJson(document.body)
        elif document.type == "glue2/teragrid/computing_shares.json":
            try:
                self.public_compute.shares = document.shares
            except AttributeError:
                self.public_compute.shares = self._parseSharesJson(document.body)
        elif document.type == "glue2/teragrid/computing_manager.json":
            try:
                self.public_compute.manager = document.manager
            except AttributeError:
                self.public_compute.manager = self._parseManagerJson(document.body)
        elif document.type == "glue2/teragrid/execution_environments.json":
            try:
                self.public_compute.environments = document.environments
            except AttributeError:
                self.public_compute.environments = self._parseEnvironmentsJson(document.body)
        else:
            self.info("ignoring unwanted input "+document.type)

    def _parseServiceJson(self, body):
        doc = json.loads(body)
        service = ComputingService()
        service.fromJson(doc)
        return service

    def _parseEndpointsJson(self, body):
        doc = json.loads(body)
        endpoints = []
        for endpoint_dict in doc:
            endpoint = ComputingEndpoint()
            endpoint.fromJson(endpoint_dict)
            endpoints.append(endpoint)
        return endpoints

    def _parseSharesJson(self, body):
        doc = json.loads(body)
        shares = []
        for share_dict in doc:
            share = ComputingShare()
            share.fromJson(share_dict)
            shares.append(share)
        return shares

    def _parseManagerJson(self, body):
        doc = json.loads(body)
        manager = ComputingManager()
        manager.fromJson(doc)
        return manager

    def _parseEnvironmentsJson(self, body):
        doc = json.loads(body)
        environments = []
        for environment_dict in doc:
            environment = ExecutionEnvironment()
            environment.fromJson(environment_dict)
            environments.append(environment)
        return environments

    def run(self):
        self.info("waiting for all inputs")
        while self.more_inputs:
            time.sleep(0.25)

        if "glue2/teragrid/public_compute.xml" in self.requested_types:
            self.engine.output(self,PublicComputeDocumentXml(self.public_compute))
        if "glue2/teragrid/public_compute.json" in self.requested_types:
            self.engine.output(self,PublicComputeDocumentJson(self.public_compute))

    def noMoreInputs(self):
        self.more_inputs = False

#######################################################################################################################

class PublicCompute(object):
    def __init__(self):
        self.resource_name = None
        self.site_name = None
        self.service = None
        self.endpoints = None
        self.shares = None
        self.manager = None
        self.environments = None

    ###################################################################################################################

    def toDom(self, hide):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "glue2",None)

        if self.resource_name is None:
            raise StepError("resource name is not set")
        e = doc.createElement("ResourceID")
        e.appendChild(doc.createTextNode(self.resource_name))
        doc.documentElement.appendChild(e)

        if self.site_name is None:
            raise StepError("site name is not set")
        e = doc.createElement("SiteID")
        e.appendChild(doc.createTextNode(self.site_name))
        doc.documentElement.appendChild(e)

        root = doc.createElement("Entities")
        doc.documentElement.appendChild(root)

        if self.service is not None:
            root.appendChild(self.service.toDom().documentElement.firstChild)
        if self.endpoints is not None:
            for endpoint in self.endpoints:
                root.appendChild(endpoint.toDom().documentElement.firstChild)
        if self.shares is not None:
            for share in self.shares:
                root.appendChild(share.toDom().documentElement.firstChild)
        if self.manager is not None:
            root.appendChild(self.manager.toDom().documentElement.firstChild)
        if self.environments is not None:
            for environment in self.environments:
                root.appendChild(environment.toDom().documentElement.firstChild)

        return doc
    
    ###################################################################################################################

    def toJson(self):
        doc = {}

        if self.resource_name is None:
            raise StepError("resource name is not set")
        doc["ResourceID"] = self.resource_name
        if self.site_name is None:
            raise StepError("site name is not set")
        doc["SiteID"] = self.site_name

        if self.service is not None:
            doc["ComputingService"] = self.service
        if self.endpoints is not None:
            doc["ComputingEndpoints"] = self.endpoints
        if self.shares is not None:
            doc["ComputingShares"] = self.shares
        if self.manager is not None:
            doc["ComputingManager"] = self.manager
        if self.environments is not None:
            doc["ExecutionEnvironments"] = self.environments
        
        return doc

    ###################################################################################################################

    def fromJson(self, doc):
        self.resource_name = doc.get("ResourceID")
        self.site_name = doc.get("SiteID")
        self.service = doc.get("ComputingService")
        self.endpoints = doc.get("ComputingEndpoints",[])
        self.shares = doc.get("ComputingShares",[])
        self.manager = doc.get("ComputingManager")
        self.environments = doc.get("ExecutionEnvironments",[])

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(PublicComputeStep())
