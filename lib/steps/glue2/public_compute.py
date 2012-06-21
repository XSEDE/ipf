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

import json
import os
from xml.dom.minidom import getDOMImplementation

from ipf.document import Document
from ipf.error import NoMoreInputsError, StepError
from ipf.step import Step

#######################################################################################################################

class PublicComputeStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "glue2/teragrid/public_compute"
        self.description = "creates a single document containing all nonsensitive compute-related information"
        self.time_out = 5
        self.requires_types = ["ipf/resource_name.txt",
                               "ipf/site_name.txt",
                               "glue2/teragrid/computing_service.json",
                               "glue2/teragrid/computing_endpoint.json",
                               "glue2/teragrid/computing_shares.json",
                               "glue2/teragrid/computing_manager.json",
                               "glue2/teragrid/execution_environments.json",]
        self.produces_types = ["glue2/teragrid/public_compute.xml",
                               "glue2/teragrid/public_compute.json"]

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        sn_doc = self._getInput("ipf/site_name.txt")
        service_doc = self._getInput("glue2/teragrid/computing_service.json")
        shares_doc = self._getInput("glue2/teragrid/computing_shares.json")
        manager_doc = self._getInput("glue2/teragrid/computing_manager.json")
        environments_doc = self._getInput("glue2/teragrid/execution_environments.json")

        endpoints = []
        try:
            while True:
                endpoint_doc = self._getInput("glue2/teragrid/computing_endpoint.json")
                endpoints.append(endpoint_doc.endpoint)
        except NoMoreInputsError:
            pass

        public_compute = PublicCompute()
        public_compute.resource_name = rn_doc.resource_name
        public_compute.site_name = sn_doc.site_name
        public_compute.service = service_doc.service
        public_compute.endpoints = endpoints
        public_compute.shares = shares_doc.shares
        public_compute.manager = manager_doc.manager
        public_compute.environments = environments_doc.exec_envs

        if "glue2/teragrid/public_compute.xml" in self.requested_types:
            self.output_queue.put(PublicComputeDocumentXml(public_compute))
        if "glue2/teragrid/public_compute.json" in self.requested_types:
            self.output_queue.put(PublicComputeDocumentJson(public_compute))

#######################################################################################################################

class PublicCompute(object):
    def __init__(self):
        self.resource_name = None
        self.site_name = None
        self.service = None
        self.endpoints = []
        self.shares = []
        self.manager = None
        self.environments = []

    ###################################################################################################################

    def toDom(self):
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
        for endpoint in self.endpoints:
            root.appendChild(endpoint.toDom().documentElement.firstChild)
        for share in self.shares:
            root.appendChild(share.toDom().documentElement.firstChild)
        if self.manager is not None:
            root.appendChild(self.manager.toDom().documentElement.firstChild)
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
            doc["ComputingService"] = self.service.toJson()
        if len(self.endpoints) > 0:
            endpoints = []
            for endpoint in self.endpoints:
                endpoints.append(endpoint.toJson())
            doc["ComputingEndpoints"] = endpoints
        if len(self.shares) > 0:
            shares = []
            for share in self.shares:
                shares.append(share.toJson())
            doc["ComputingShares"] = shares
        if self.manager is not None:
            doc["ComputingManager"] = self.manager.toJson()
        if len(self.environments) > 0:
            envs = []
            for env in self.environments:
                envs.append(env.toJson())
            doc["ExecutionEnvironments"] = envs
        
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

class PublicComputeDocumentXml(Document):
    def __init__(self, public_compute):
        Document.__init__(self, public_compute.resource_name, "glue2/teragrid/public_compute.xml")
        self.public_compute = public_compute

    def _setBody(self, body):
        raise DocumentError("PublicComputeDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        return self.public_compute.toDom().toxml()

#######################################################################################################################

class PublicComputeDocumentJson(Document):
    def __init__(self, public_compute):
        Document.__init__(self, public_compute.resource_name, "glue2/teragrid/public_compute.json")
        self.public_compute = public_compute

    def _setBody(self, body):
        self.public_compute = PublicCompute()
        self.public_compute.fromJson(json.loads(body))

    def _getBody(self):
        return json.dumps(self.public_compute.toJson(),indent=4)

#######################################################################################################################
