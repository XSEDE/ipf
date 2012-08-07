
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

import json
import os
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
#from ipf.dt import *
from ipf.error import NoMoreInputsError, StepError
from ipf.resource_name import ResourceName
from ipf.site_name import SiteName
from ipf.step import Step

from glue2.computing_endpoint import ComputingEndpoint, ComputingEndpointTeraGridXml, ComputingEndpointIpfJson
from glue2.computing_manager import ComputingManager, ComputingManagerTeraGridXml, ComputingManagerIpfJson
from glue2.computing_service import ComputingService, ComputingServiceTeraGridXml, ComputingServiceIpfJson
from glue2.computing_share import ComputingShares, ComputingShareTeraGridXml, ComputingShareIpfJson
from glue2.execution_environment import ExecutionEnvironments, ExecutionEnvironmentTeraGridXml
from glue2.execution_environment import ExecutionEnvironmentTeraGridXml
from glue2.execution_environment import ExecutionEnvironmentIpfJson

#######################################################################################################################

class PublicComputeStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all nonsensitive compute-related information"
        self.time_out = 5
        self.requires = [ResourceName,SiteName,
                         ComputingService,ComputingEndpoint,ComputingShares,ComputingManager,ExecutionEnvironments]
        self.produces = [PublicCompute]

    def run(self):
        public_compute = PublicCompute()
        public_compute.resource_name = self._getInput(ResourceName).resource_name
        public_compute.site_name = self._getInput(SiteName).site_name
        public_compute.service = self._getInput(ComputingService)
        public_compute.shares = self._getInput(ComputingShares).shares
        public_compute.manager = self._getInput(ComputingManager)
        public_compute.environments = self._getInput(ExecutionEnvironments).exec_envs
        try:
            while True:
                public_compute.endpoints.append(self._getInput(ComputingEndpoint))
        except NoMoreInputsError:
            pass
        public_compute.id = public_compute.resource_name

        self._output(public_compute)

#######################################################################################################################

class PublicCompute(Data):
    def __init__(self):
        Data.__init__(self)

        #self.CreationTime = datetime.datetime.now(tzoffset(0))

        self.resource_name = None
        self.site_name = None
        self.service = None
        self.endpoints = []
        self.shares = []
        self.manager = None
        self.environments = []

    def fromJson(self, doc):
        #if "CreationTime" in doc:
        #    self.CreationTime = textToDateTime(doc["CreationTime"])
        #else:
        #    self.CreationTime = None
        self.resource_name = doc.get("ResourceID")
        self.site_name = doc.get("SiteID")
        self.service = doc.get("ComputingService")
        self.endpoints = doc.get("ComputingEndpoints",[])
        self.shares = doc.get("ComputingShares",[])
        self.manager = doc.get("ComputingManager")
        self.environments = doc.get("ExecutionEnvironments",[])

#######################################################################################################################

class PublicComputeTeraGridXml(Representation):
    data_cls = PublicCompute

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(public_compute):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "glue2",None)

        if public_compute.resource_name is None:
            raise StepError("resource name is not set")
        e = doc.createElement("ResourceID")
        e.appendChild(doc.createTextNode(public_compute.resource_name))
        doc.documentElement.appendChild(e)

        if public_compute.site_name is None:
            raise StepError("site name is not set")
        e = doc.createElement("SiteID")
        e.appendChild(doc.createTextNode(public_compute.site_name))
        doc.documentElement.appendChild(e)

        root = doc.createElement("Entities")
        doc.documentElement.appendChild(root)

        if public_compute.service is not None:
            root.appendChild(ComputingServiceTeraGridXml.toDom(public_compute.service).documentElement.firstChild)
        for endpoint in public_compute.endpoints:
            root.appendChild(ComputingEndpointTeraGridXml.toDom(endpoint).documentElement.firstChild)
        for share in public_compute.shares:
            root.appendChild(ComputingShareTeraGridXml.toDom(share).documentElement.firstChild)
        if public_compute.manager is not None:
            root.appendChild(ComputingManagerTeraGridXml.toDom(public_compute.manager).documentElement.firstChild)
        for environment in public_compute.environments:
            root.appendChild(ExecutionEnvironmentTeraGridXml.toDom(environment).documentElement.firstChild)

        return doc

#######################################################################################################################

class PublicComputeIpfJson(Representation):
    data_cls = PublicCompute

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),indent=4)

    @staticmethod
    def toJson(public_compute):
        doc = {}

        if public_compute.resource_name is None:
            raise StepError("resource name is not set")
        doc["ResourceID"] = public_compute.resource_name
        if public_compute.site_name is None:
            raise StepError("site name is not set")
        doc["SiteID"] = public_compute.site_name

        if public_compute.service is not None:
            doc["ComputingService"] = ComputingServiceIpfJson.toJson(public_compute.service)
        if len(public_compute.endpoints) > 0:
            endpoints = []
            for endpoint in public_compute.endpoints:
                endpoints.append(ComputingEndpointIpfJson.toJson(endpoint))
            doc["ComputingEndpoints"] = endpoints
        if len(public_compute.shares) > 0:
            shares = []
            for share in public_compute.shares:
                shares.append(ComputingShareIpfJson.toJson(share))
            doc["ComputingShares"] = shares
        if public_compute.manager is not None:
            doc["ComputingManager"] = ComputingManagerIpfJson.toJson(public_compute.manager)
        if len(public_compute.environments) > 0:
            envs = []
            for env in public_compute.environments:
                envs.append(ExecutionEnvironmentIpfJson.toJson(env))
            doc["ExecutionEnvironments"] = envs
        
        return doc

#######################################################################################################################
