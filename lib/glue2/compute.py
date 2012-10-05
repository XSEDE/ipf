
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
from ipf.name import ResourceName
from ipf.step import Step

from glue2.computing_activity import ComputingActivities, ComputingActivityTeraGridXml, ComputingActivityIpfJson
from glue2.computing_endpoint import ComputingEndpoint, ComputingEndpointTeraGridXml, ComputingEndpointIpfJson
from glue2.computing_manager import ComputingManager, ComputingManagerTeraGridXml, ComputingManagerIpfJson
from glue2.computing_service import ComputingService, ComputingServiceTeraGridXml, ComputingServiceIpfJson
from glue2.computing_share import ComputingShares, ComputingShareTeraGridXml, ComputingShareIpfJson
from glue2.execution_environment import ExecutionEnvironments, ExecutionEnvironmentTeraGridXml
from glue2.execution_environment import ExecutionEnvironmentTeraGridXml
from glue2.execution_environment import ExecutionEnvironmentIpfJson
from glue2.location import Location, LocationIpfJson

#######################################################################################################################

class PublicStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all nonsensitive compute-related information"
        self.time_out = 5
        self.requires = [ResourceName,Location,
                         ComputingService,ComputingEndpoint,ComputingShares,ComputingManager,ExecutionEnvironments]
        self.produces = [Public]

    def run(self):
        public = Public()
        public.resource_name = self._getInput(ResourceName).resource_name
        public.location = self._getInput(Location)
        public.service = self._getInput(ComputingService)
        public.shares = self._getInput(ComputingShares).shares
        public.manager = self._getInput(ComputingManager)
        public.environments = self._getInput(ExecutionEnvironments).exec_envs
        try:
            while True:
                public.endpoints.append(self._getInput(ComputingEndpoint))
        except NoMoreInputsError:
            pass
        public.id = public.resource_name

        self._output(public)

#######################################################################################################################

class Public(Data):
    def __init__(self):
        Data.__init__(self)

        self.resource_name = None
        self.location = None
        self.service = None
        self.endpoints = []
        self.shares = []
        self.manager = None
        self.environments = []

    def fromJson(self, doc):
        self.resource_name = doc.get("ResourceID")
        self.location = Location().fromJson(doc.get("Location"))
        self.service = ComputingService().fromJson(doc.get("ComputingService"))
        self.endpoints = []
        for edoc in doc.get("ComputingEndpoints",[]):
            self.endpoints.append(ComputingEndpoint().fromJson(edoc))
        self.shares = []
        for sdoc in doc.get("ComputingShares",[]):
            self.shares.append(ComputingShare().fromJson(sdoc))
        self.manager = ComputingManager().fromJson(doc.get("ComputingManager"))
        self.environments = []
        for edoc in doc.get("ExecutionEnvironments",[]):
            self.environments.append(ExecutionEnvironment().fromJson(edoc))

#######################################################################################################################

class PublicTeraGridXml(Representation):
    data_cls = Public

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(public):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "glue2",None)
        root = doc.createElement("Entities")
        doc.documentElement.appendChild(root)

        if public.location is not None:
            root.appendChild(LocationTeraGridXML.toDom(public.location).document.firstChild)
        if public.service is not None:
            root.appendChild(ComputingServiceTeraGridXml.toDom(public.service).documentElement.firstChild)
        for endpoint in public.endpoints:
            root.appendChild(ComputingEndpointTeraGridXml.toDom(endpoint).documentElement.firstChild)
        for share in public.shares:
            root.appendChild(ComputingShareTeraGridXml.toDom(share).documentElement.firstChild)
        if public.manager is not None:
            root.appendChild(ComputingManagerTeraGridXml.toDom(public.manager).documentElement.firstChild)
        for environment in public.environments:
            root.appendChild(ExecutionEnvironmentTeraGridXml.toDom(environment).documentElement.firstChild)

        return doc

#######################################################################################################################

class PublicIpfJson(Representation):
    data_cls = Public

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),indent=4)

    @staticmethod
    def toJson(public):
        doc = {}

        if public.location is not None:
            doc["Location"] = LocationIpfJson.toJson(public.location)
        if public.service is not None:
            doc["ComputingService"] = ComputingServiceIpfJson.toJson(public.service)
        if len(public.endpoints) > 0:
            endpoints = []
            for endpoint in public.endpoints:
                endpoints.append(ComputingEndpointIpfJson.toJson(endpoint))
            doc["ComputingEndpoints"] = endpoints
        if len(public.shares) > 0:
            shares = []
            for share in public.shares:
                shares.append(ComputingShareIpfJson.toJson(share))
            doc["ComputingShares"] = shares
        if public.manager is not None:
            doc["ComputingManager"] = ComputingManagerIpfJson.toJson(public.manager)
        if len(public.environments) > 0:
            envs = []
            for env in public.environments:
                envs.append(ExecutionEnvironmentIpfJson.toJson(env))
            doc["ExecutionEnvironments"] = envs
        
        return doc

#######################################################################################################################

class PrivateStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all sensitive compute-related information"
        self.time_out = 5
        self.requires = [ResourceName,Location,ComputingActivities]
        self.produces = [Private]

    def run(self):
        private = Private()
        private.resource_name = self._getInput(ResourceName).resource_name
        private.location = self._getInput(Location)
        private.activities = self._getInput(ComputingActivities).activities
        private.id = private.resource_name
        
        self._output(private)

#######################################################################################################################

class Private(Data):
    def __init__(self):
        Data.__init__(self)

        self.resource_name = None
        self.location = None
        self.activities = []

    def fromJson(self, doc):
        self.resource_name = doc.get("ResourceID")
        self.location = doc.get("Location")
        self.activities = doc.get("ComputingActivities",[])

#######################################################################################################################

class PrivateTeraGridXml(Representation):
    data_cls = Private

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(private):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "glue2",None)

        root = doc.createElement("Entities")
        doc.documentElement.appendChild(root)

        for activity in private.activities:
            root.appendChild(ComputingActivityTeraGridXml.toDom(activity).documentElement.firstChild)
        return doc


#######################################################################################################################

class PrivateIpfJson(Representation):
    data_cls = Private

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),indent=4)

    @staticmethod
    def toJson(private):
        doc = {}

        if len(private.activities) > 0:
            docs = []
            for activity in private.activities:
                docs.append(ComputingActivityIpfJson.toJson(activity))
            doc["ComputingActivities"] = docs
        
        return doc

#######################################################################################################################
