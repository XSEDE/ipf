
###############################################################################
#   Copyright 2011-2014 The University of Texas at Austin                     #
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
from ipf.sysinfo import ResourceName
from ipf.step import Step

from ipf.ipfinfo import IPFInformation, IPFInformationJson, IPFInformationTxt
from .computing_activity import ComputingActivities, ComputingActivityTeraGridXml, ComputingActivityOgfJson
from .computing_manager import ComputingManager, ComputingManagerTeraGridXml, ComputingManagerOgfJson
from .computing_manager_accel_info import ComputingManagerAcceleratorInfo, ComputingManagerAcceleratorInfoOgfJson
from .computing_service import ComputingService, ComputingServiceTeraGridXml, ComputingServiceOgfJson
from .computing_share import ComputingShares, ComputingShareTeraGridXml, ComputingShareOgfJson
from .computing_share_accel_info import ComputingShareAcceleratorInfo, ComputingShareAcceleratorInfoOgfJson
from .execution_environment import ExecutionEnvironments, ExecutionEnvironmentTeraGridXml
from .execution_environment import ExecutionEnvironmentTeraGridXml
from .execution_environment import ExecutionEnvironmentOgfJson
from .accelerator_environment import AcceleratorEnvironments
from .accelerator_environment import AcceleratorEnvironmentsOgfJson
from .accelerator_environment import AcceleratorEnvironment
from .accelerator_environment import AcceleratorEnvironmentOgfJson
from .location import Location, LocationOgfJson, LocationTeraGridXml
#######################################################################################################################


class PublicStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all nonsensitive compute-related information"
        self.time_out = 5
        self.requires = [IPFInformation, ResourceName, Location,
                         ComputingService, ComputingShares, ComputingManager, ExecutionEnvironments, AcceleratorEnvironments, ComputingManagerAcceleratorInfo, ComputingShareAcceleratorInfo]
        self.produces = [Public]

    def run(self):
        public = Public()
        public.resource_name = self._getInput(ResourceName).resource_name
        public.ipfinfo = [self._getInput(IPFInformation)]
        # the old TeraGridXML wants a site_name, so just derive it
        public.site_name = public.resource_name[public.resource_name.find(
            ".")+1:]
        public.location = [self._getInput(Location)]
        public.service = [self._getInput(ComputingService)]
        public.share = self._getInput(ComputingShares).shares
        public.manager = [self._getInput(ComputingManager)]
        public.manager_accel_info = [
            self._getInput(ComputingManagerAcceleratorInfo)]
        public.share_accel_info = [
            self._getInput(ComputingShareAcceleratorInfo)]
        public.environment = self._getInput(ExecutionEnvironments).exec_envs
        public.accelenvironment = self._getInput(
            AcceleratorEnvironments).accel_envs
        public.id = public.resource_name

        self._output(public)

#######################################################################################################################


class Public(Data):
    def __init__(self):
        Data.__init__(self)

        self.ipfinfo = []
        self.location = []
        self.service = []
        self.share = []
        self.manager = []
        self.environment = []
        self.accelenvironment = []

    def fromJson(self, doc):
        self.ipfinfo = []
        for idoc in doc.get("Ipfinfo", []):
            self.ipfinfo.append(ipfinfo().fromJson(idoc))
        self.location = []
        for ldoc in doc.get("Location", []):
            self.location.append(Location().fromJson(ldoc))
        self.service = []
        for sdoc in doc.get("ComputingService"):
            self.service.append(ComputingService().fromJson(sdoc))
        self.share = []
        for sdoc in doc.get("ComputingShare", []):
            self.share.append(ComputingShare().fromJson(sdoc))
        self.manager = []
        for mdoc in doc.get("ComputingManager"):
            self.manager.append(ComputingManager().fromJson(mdoc))
        self.environment = []
        for edoc in doc.get("ExecutionEnvironment", []):
            self.environment.append(ExecutionEnvironment().fromJson(edoc))
        self.accleenvironment = []
        for edoc in doc.get("AcceleratorEnvironment", []):
            self.environment.append(AcceleratorEnvironment().fromJson(edoc))

#######################################################################################################################


class PublicTeraGridXml(Representation):
    data_cls = Public

    def __init__(self, data):
        Representation.__init__(self, Representation.MIME_TEXT_XML, data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/2009/03/ctss",
                                                    "V4glue2RP", None)
        # hack - minidom doesn't output name spaces
        doc.documentElement.setAttribute(
            "xmlns", "http://info.teragrid.org/2009/03/ctss")

        glue2 = doc.createElementNS(
            "http://info.teragrid.org/glue/2009/02/spec_2.0_r02", "glue2")
        doc.documentElement.appendChild(glue2)
        # WS-MDS doesn't want a namespace on glue2
        # setAttribute("xmlns","http://info.teragrid.org/glue/2009/02/spec_2.0_r02")
        setAttribute("Timestamp", dateTimeToText(
            self.data.manager[0].CreationTime))
        setAttribute("UniqueID", ""+self.data.resource_name)
        resource = doc.createElement("ResourceID")
        resource.appendChild(doc.createTextNode(self.data.resource_name))
        appendChild(resource)
        site = doc.createElement("SiteID")
        site.appendChild(doc.createTextNode(self.data.site_name))
        appendChild(site)

        entities = doc.createElement("Entities")
        appendChild(entities)

        for location in self.data.location:
            entities.appendChild(LocationTeraGridXml(
                location).toDom().documentElement.firstChild)
        for service in self.data.service:
            entities.appendChild(ComputingServiceTeraGridXml(
                service).toDom().documentElement.firstChild)
        for share in self.data.share:
            entities.appendChild(ComputingShareTeraGridXml(
                share).toDom().documentElement.firstChild)
        for manager in self.data.manager:
            entities.appendChild(ComputingManagerTeraGridXml(
                manager).toDom().documentElement.firstChild)
        for environment in self.data.environment:
            entities.appendChild(ExecutionEnvironmentTeraGridXml(
                environment).toDom().documentElement.firstChild)

        return doc

#######################################################################################################################


class PublicOgfJson(Representation):
    data_cls = Public

    def __init__(self, data):
        Representation.__init__(
            self, Representation.MIME_APPLICATION_JSON, data)

    def get(self):
        return json.dumps(self.toJson(), indent=4)

    def toJson(self):
        doc = {}

        if self.data.ipfinfo is not None:
            doc["PublisherInfo"] = [IPFInformationJson(
                ipfinfo).toJson() for ipfinfo in self.data.ipfinfo]
        if len(self.data.location) > 0:
            doc["Location"] = [LocationOgfJson(
                location).toJson() for location in self.data.location]
        if self.data.service is not None:
            doc["ComputingService"] = [ComputingServiceOgfJson(
                service).toJson() for service in self.data.service]
        if len(self.data.share) > 0:
            doc["ComputingShare"] = [ComputingShareOgfJson(
                share).toJson() for share in self.data.share]
        if len(self.data.share_accel_info) > 0:
            csai = [ComputingShareAcceleratorInfoOgfJson(
                exec_env).toJson() for exec_env in self.data.share_accel_info]
            csaii = list([_f for _f in csai if _f])
            if len(csaii) > 0:
                doc["ComputingShareAcceleratorInfo"] = csaii
        if len(self.data.manager) > 0:
            doc["ComputingManager"] = [ComputingManagerOgfJson(
                manager).toJson() for manager in self.data.manager]
        if len(self.data.environment) > 0:
            doc["ExecutionEnvironment"] = [ExecutionEnvironmentOgfJson(
                exec_env).toJson() for exec_env in self.data.environment]
        if self.data.accelenvironment:
            if len(self.data.accelenvironment) > 0:
                doc["AcceleratorEnvironment"] = [AcceleratorEnvironmentOgfJson(
                    exec_env).toJson() for exec_env in self.data.accelenvironment]
        if len(self.data.manager_accel_info) > 0:
            cmai = [ComputingManagerAcceleratorInfoOgfJson(
                exec_env).toJson() for exec_env in self.data.manager_accel_info]
            cmaii = list([_f for _f in cmai if _f])
            if len(cmaii) > 0:
                doc["ComputingManagerAcceleratorInfo"] = cmaii

        return doc

#######################################################################################################################


class PrivateStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all sensitive compute-related information"
        self.time_out = 5
        self.requires = [IPFInformation, ResourceName, ComputingActivities]
        self.produces = [Private]

    def run(self):
        private = Private()
        private.ipfinfo = [self._getInput(IPFInformation)]
        private.resource_name = self._getInput(ResourceName).resource_name
        # the old TeraGridXML wants a site_name, so just derive it
        private.site_name = private.resource_name[private.resource_name.find(
            ".")+1:]
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
        for adoc in doc.get("ComputingActivity", []):
            self.location.append(ComputingActivity().fromJson(adoc))

#######################################################################################################################


class PrivateTeraGridXml(Representation):
    data_cls = Private

    def __init__(self, data):
        Representation.__init__(self, Representation.MIME_TEXT_XML, data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/2009/03/ctss",
                                                    "V4glue2RP", None)
        # hack - minidom doesn't output name spaces
        doc.documentElement.setAttribute(
            "xmlns", "http://info.teragrid.org/2009/03/ctss")

        glue2 = doc.createElementNS(
            "http://info.teragrid.org/glue/2009/02/spec_2.0_r02", "glue2")
        doc.documentElement.appendChild(glue2)
        # WS-MDS doesn't want a namespace on glue2
        # setAttribute("xmlns","http://info.teragrid.org/glue/2009/02/spec_2.0_r02")
        if len(self.data.activity) > 0:
            setAttribute("Timestamp", dateTimeToText(
                self.data.activity[0].CreationTime))
        else:
            setAttribute("Timestamp", dateTimeToText(
                datetime.datetime.now(tzoffset(0))))
        setAttribute("UniqueID", ""+self.data.resource_name)
        resource = doc.createElement("ResourceID")
        resource.appendChild(doc.createTextNode(self.data.resource_name))
        appendChild(resource)
        site = doc.createElement("SiteID")
        site.appendChild(doc.createTextNode(self.data.site_name))
        appendChild(site)

        entities = doc.createElement("Entities")
        appendChild(entities)

        for activity in self.data.activity:
            entities.appendChild(ComputingActivityTeraGridXml(
                activity).toDom().documentElement.firstChild)
        return doc


#######################################################################################################################

class PrivateOgfJson(Representation):
    data_cls = Private

    def __init__(self, data):
        Representation.__init__(
            self, Representation.MIME_APPLICATION_JSON, data)

    def get(self):
        return json.dumps(self.toJson(), indent=4)

    def toJson(self):
        doc = {}
        if len(self.data.activity) > 0:
            doc["ComputingActivity"] = [ComputingActivityOgfJson(
                activity).toJson() for activity in self.data.activity]
        doc["PublisherInfo"] = [IPFInformationJson(
            ipfinfo).toJson() for ipfinfo in self.data.ipfinfo]
        return doc

#######################################################################################################################
