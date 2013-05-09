
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
from ipf.dt import *
from ipf.error import NoMoreInputsError, StepError
from ipf.sysinfo import ResourceName,SiteName
from ipf.step import Step

from glue2.computing_activity import ComputingActivities, ComputingActivityTeraGridXml, ComputingActivityIpfJson
from glue2.computing_endpoint import ComputingEndpoint, ComputingEndpointTeraGridXml, ComputingEndpointIpfJson
from glue2.computing_manager import ComputingManager, ComputingManagerTeraGridXml, ComputingManagerIpfJson
from glue2.computing_service import ComputingService, ComputingServiceTeraGridXml, ComputingServiceIpfJson
from glue2.computing_share import ComputingShares, ComputingShareTeraGridXml, ComputingShareIpfJson
from glue2.execution_environment import ExecutionEnvironments, ExecutionEnvironmentTeraGridXml
from glue2.execution_environment import ExecutionEnvironmentTeraGridXml
from glue2.execution_environment import ExecutionEnvironmentIpfJson
from glue2.location import Location, LocationIpfJson, LocationTeraGridXml

#######################################################################################################################

class PublicStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all nonsensitive compute-related information"
        self.time_out = 5
        # TeraGridXML requires SiteName
        self.requires = [ResourceName,SiteName,Location,
                         ComputingService,ComputingEndpoint,ComputingShares,ComputingManager,ExecutionEnvironments]
        self.produces = [Public]

    def run(self):
        public = Public()
        public.resource_name = self._getInput(ResourceName).resource_name
        public.site_name = self._getInput(SiteName).site_name
        public.location = [self._getInput(Location)]
        public.service = [self._getInput(ComputingService)]
        public.share = self._getInput(ComputingShares).shares
        public.manager = [self._getInput(ComputingManager)]
        public.environment = self._getInput(ExecutionEnvironments).exec_envs
        try:
            while True:
                public.endpoint.append(self._getInput(ComputingEndpoint))
        except NoMoreInputsError:
            pass
        public.id = public.resource_name

        self._output(public)

#######################################################################################################################

class Public(Data):
    def __init__(self):
        Data.__init__(self)

        self.location = []
        self.service = []
        self.endpoint = []
        self.share = []
        self.manager = []
        self.environment = []

    def fromJson(self, doc):
        self.location = []
        for ldoc in doc.get("Location",[]):
            self.location.append(Location().fromJson(ldoc))
        self.service = []
        for sdoc in doc.get("ComputingService"):
            self.service.append(ComputingService().fromJson(sdoc))
        self.endpoint = []
        for edoc in doc.get("ComputingEndpoint",[]):
            self.endpoint.append(ComputingEndpoint().fromJson(edoc))
        self.share = []
        for sdoc in doc.get("ComputingShare",[]):
            self.share.append(ComputingShare().fromJson(sdoc))
        self.manager = []
        for mdoc in doc.get("ComputingManager"):
            self.manager.append(ComputingManager().fromJson(mdoc))
        self.environment = []
        for edoc in doc.get("ExecutionEnvironment",[]):
            self.environment.append(ExecutionEnvironment().fromJson(edoc))

#######################################################################################################################

class PublicTeraGridXml(Representation):
    data_cls = Public

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(public):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/2009/03/ctss",
                                                    "V4glue2RP",None)
        # hack - minidom doesn't output name spaces
        doc.documentElement.setAttribute("xmlns","http://info.teragrid.org/2009/03/ctss")

        glue2 = doc.createElementNS("http://info.teragrid.org/glue/2009/02/spec_2.0_r02","glue2")
        doc.documentElement.appendChild(glue2)
        # WS-MDS doesn't want a namespace on glue2
        #glue2.setAttribute("xmlns","http://info.teragrid.org/glue/2009/02/spec_2.0_r02")
        glue2.setAttribute("Timestamp",dateTimeToText(public.manager[0].CreationTime))
        glue2.setAttribute("UniqueID","glue2."+public.resource_name)
        resource = doc.createElement("ResourceID")
        resource.appendChild(doc.createTextNode(public.resource_name))
        glue2.appendChild(resource)
        site = doc.createElement("SiteID")
        site.appendChild(doc.createTextNode(public.site_name))
        glue2.appendChild(site)

        entities = doc.createElement("Entities")
        glue2.appendChild(entities)

        for location in public.location:
            entities.appendChild(LocationTeraGridXml.toDom(location).documentElement.firstChild)
        for service in public.service:
            entities.appendChild(ComputingServiceTeraGridXml.toDom(service).documentElement.firstChild)
        for endpoint in public.endpoint:
            entities.appendChild(ComputingEndpointTeraGridXml.toDom(endpoint).documentElement.firstChild)
        for share in public.share:
            entities.appendChild(ComputingShareTeraGridXml.toDom(share).documentElement.firstChild)
        for manager in public.manager:
            entities.appendChild(ComputingManagerTeraGridXml.toDom(manager).documentElement.firstChild)
        for environment in public.environment:
            entities.appendChild(ExecutionEnvironmentTeraGridXml.toDom(environment).documentElement.firstChild)

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

        if len(public.location) > 0:
            doc["Location"] = map(LocationIpfJson.toJson,public.location)
        if public.service is not None:
            doc["ComputingService"] = map(ComputingServiceIpfJson.toJson,public.service)
        if len(public.endpoint) > 0:
            doc["ComputingEndpoint"] = map(ComputingEndpointIpfJson.toJson,public.endpoint)
        if len(public.share) > 0:
            doc["ComputingShare"] = map(ComputingShareIpfJson.toJson,public.share)
        if len(public.manager) > 0:
            doc["ComputingManager"] = map(ComputingManagerIpfJson.toJson,public.manager)
        if len(public.environment) > 0:
            doc["ExecutionEnvironment"] = map(ExecutionEnvironmentIpfJson.toJson,public.environment)
        
        return doc

#######################################################################################################################

class PrivateStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all sensitive compute-related information"
        self.time_out = 5
        # TeraGridXML requires SiteName
        self.requires = [ResourceName,SiteName,ComputingActivities]
        self.produces = [Private]

    def run(self):
        private = Private()
        private.resource_name = self._getInput(ResourceName).resource_name
        private.site_name = self._getInput(SiteName).site_name
        private.activity = self._getInput(ComputingActivities).activities
        private.id = private.resource_name
        
        self._output(private)

#######################################################################################################################

class Private(Data):
    def __init__(self):
        Data.__init__(self)

        self.activity = []

    def fromJson(self, doc):
        self.activity = []
        for adoc in doc.get("ComputingActivity",[]):
            self.location.append(ComputingActivity().fromJson(adoc))

#######################################################################################################################

class PrivateTeraGridXml(Representation):
    data_cls = Private

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(private):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/2009/03/ctss",
                                                    "V4glue2RP",None)
        # hack - minidom doesn't output name spaces
        doc.documentElement.setAttribute("xmlns","http://info.teragrid.org/2009/03/ctss")

        glue2 = doc.createElementNS("http://info.teragrid.org/glue/2009/02/spec_2.0_r02","glue2")
        doc.documentElement.appendChild(glue2)
        # WS-MDS doesn't want a namespace on glue2
        #glue2.setAttribute("xmlns","http://info.teragrid.org/glue/2009/02/spec_2.0_r02")
        if len(private.activity) > 0:
            glue2.setAttribute("Timestamp",dateTimeToText(private.activity[0].CreationTime))
        else:
            glue2.setAttribute("Timestamp",dateTimeToText(datetime.datetime.now(tzoffset(0))))
        glue2.setAttribute("UniqueID","glue2."+private.resource_name)
        resource = doc.createElement("ResourceID")
        resource.appendChild(doc.createTextNode(private.resource_name))
        glue2.appendChild(resource)
        site = doc.createElement("SiteID")
        site.appendChild(doc.createTextNode(private.site_name))
        glue2.appendChild(site)

        entities = doc.createElement("Entities")
        glue2.appendChild(entities)

        for activity in private.activity:
            entities.appendChild(ComputingActivityTeraGridXml.toDom(activity).documentElement.firstChild)
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
        if len(private.activity) > 0:
            doc["ComputingActivity"] = map(ComputingActivityIpfJson.toJson,private.activity)
        return doc

#######################################################################################################################
