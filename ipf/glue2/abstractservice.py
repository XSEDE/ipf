
###############################################################################
#   Copyright 2012-2014 The University of Texas at Austin                     #
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

import subprocess
import datetime
import os
import re
import pprint
import hashlib

from ipf.dt import localtzoffset
from ipf.error import StepError
from ipf.log import LogDirectoryWatcher

from . import computing_manager
from . import service
#from . import computing_share
from . import execution_environment
from ipf.step import Step
import json
#from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation

from .entity import *
from .service import *
from .endpoint import *
from ipf.sysinfo import ResourceName
from ipf.ipfinfo import IPFInformation, IPFInformationJson, IPFInformationTxt


#######################################################################################################################
class AbstractService(Data):
    def __init__(self, id, ipfinfo):
        Data.__init__(self, id)
        self.services = []
        self.handles = []
        self.ipfinfo = ipfinfo

    def add(self, serv):
        self.services.append(serv)


class AbstractServiceStep(Step):

    def __init__(self):
        Step.__init__(self)
        self.requires = [IPFInformation, ResourceName]
        self.produces = [AbstractService]
        self.services = []

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.ipfinfo = [self._getInput(IPFInformation)]
        servlist = AbstractService(self.resource_name, self.ipfinfo)
        service_paths = []
        try:
            paths = os.environ["SERVICEPATH"]
            service_paths.extend(paths.split(":"))
        except KeyError:
            raise StepError("didn't find environment variable SERVICEPATH")

        for path in service_paths:
            try:
                packages = os.listdir(path)
            except OSError:
                continue
            for name in packages:
                #print("name of package is" +name)
                #print("path is " +path)
                if name.startswith("."):
                    continue
                if name.endswith("~"):
                    continue
                if name.endswith(".lua"):
                    self._addService(os.path.join(path, name), path, serv)
                else:
                    self.info("calling addmodule w/ version")
                    #print("calling addmodule w/ version")
                    serv = service.Service()
                    self._addService(os.path.join(path, name), path, servlist)

        self._output(servlist)

    def _addService(self, path, name, servlist):

        serv = service.Service()
        ServiceType = ""
        try:
            file = open(path)
        except IOError as e:
            self.warning("%s" % e)
            return
        text = file.read()
        file.close()
        #print("in correct _addService")
        m = re.search("Name = ([^\ ]+)\n", text)
        if m is not None:
            serv.Name = m.group(1).strip()
            # print(serv.Name)
        else:
            self.debug("no name in "+path)
            #print("no name in "+path)
        m = re.search("Name = ([^\ ]+)\n", text)
        if m is not None:
            serv.Type = m.group(1).strip()
            # print(serv.Type)
        else:
            self.debug("no type in "+path)
            #print("no type in "+path)
        m = re.search("Version = ([^\ ]+)\n", text)
        if m is not None:
            serv.Version = m.group(1).strip()
            # print(serv.Version)
        else:
            self.debug("no Version in "+path)
            #print("no Version in "+path)
        m = re.search("Endpoint = ([^\ ]+)\ *\n", text)
        if m is not None:
            serv.Endpoint = m.group(1).strip()
            #print("SERV ENDPOINT IS " +serv.Endpoint)
        else:
            self.debug("no endpoint in "+path)
            serv.Endpoint = ""
            #print("no endpoint in "+path)
        m = re.findall("Capability = ([^\ ]+)\n", text)
        if m is not None:
            if serv.Capability is not None:
                serv.Capability.append(m.group(1).lower().strip())
            else:
                mlower = []
                for cap in m:
                    mlower.append(cap.lower())
                serv.Capability = mlower
        else:
            self.debug("no Capability in "+path)
            #print("no capability in "+path)
        m = re.search("SupportStatus = ([^\ ]+)\n", text)
        if m is not None:
            serv.QualityLevel = m.group(1).strip()
        else:
            self.debug("no support status in "+path)
            #print("no support status in "+path)
        m = re.search("QualityLevel = ([^\ ]+)\n", text)
        if m is not None:
            serv.QualityLevel = m.group(1).strip()
        else:
            self.debug("no qualitylevel in "+path)
            #print("no qualitylevel in "+path)
        m = re.search("Keywords = ([^\ ]+)\n", text)
        if m is not None:
            serv.Extension["Keywords"] = list(
                map(str.strip, m.group(1).split(",")))
        else:
            self.debug("no keywords in "+path)
            #print("no keywords in "+path)
        #n = re.finditer("Extensions.(.*?) = ([^\ ]+)\n",text)
        n = re.finditer("Extensions.(.*?) = (.*?)\n", text)
        for match in n:
            serv.Extension[match.group(1).strip()] = match.group(2).strip()

        st = serv.Capability[0].split(".")
        #print("st is %s", st)
        if st[0] == "data":
            ServiceType = "StorageService"
        else:
            if st[0] == "information":
                ServiceType = "InformationService"
            else:
                if st[0] == "executionmanagement":
                    ServiceType = "ComputingService"
                else:
                    if st[0] == "information":
                        ServiceType = "InformationService"
                    else:
                        if st[0] == "login":
                            ServiceType = "LoginService"
                        else:
                            ServiceType = "UntypedService"
        serv.resource_name = self.resource_name
        endpointhash = ''
        if (serv.Endpoint != ''):
            endpointhashobject = hashlib.md5(str(serv.Endpoint).encode('utf-8'))
            endpointhash = "-"+endpointhashobject.hexdigest()
        serv.ID = "urn:ogf:ogf:glue2:xsede.org:%s:%s-%s%s" % (ServiceType,
                                            serv.Name, self.resource_name, endpointhash)
        serv.ServiceType = ServiceType
        servlist.add(serv)

#######################################################################################################################


class AbstractServiceOgfJson(EntityOgfJson):
    data_cls = Service

    def __init__(self, data):
        EntityOgfJson.__init__(self, data)

    def get(self):
        return json.dumps(self.toJson(), sort_keys=True, indent=4)

    def toJson(self):
        doc = {}
        doc = EntityOgfJson.toJson(self)

        #print("in AbstractServiceOgfJson toJson")
        if len(self.data.Capability) > 0:
            doc["Capability"] = self.data.Capability
        if self.data.Type is not None:
            doc["Type"] = self.data.Type
        if self.data.QualityLevel is not None:
            doc["QualityLevel"] = self.data.QualityLevel
        if len(self.data.StatusInfo) > 0:
            doc["StatusInfo"] = self.data.StatusInfo
        if self.data.Complexity is not None:
            doc["Complexity"] = self.data.Complexity

        associations = {}
        if len(self.data.EndpointID) > 0:
            associations["EndpointID"] = self.data.EndpointID
        if len(self.data.ShareID) > 0:
            associations["ShareID"] = self.data.ShareID
        if len(self.data.ManagerID) > 0:
            associations["ManagerID"] = self.data.ManagerID
            associations["ContactID"] = self.data.ContactID
            associations["LocationID"] = self.data.LocationID
            associations["ServiceID"] = self.data.ServiceID
        doc["Associations"] = associations

        return doc


class ASOgfJson(Representation):
    data_cls = AbstractService

    def __init__(self, data):
        Representation.__init__(
            self, Representation.MIME_APPLICATION_JSON, data)

    def get(self):
        return json.dumps(self.toJson(), sort_keys=True, indent=4)

    def toJson(self):
        doc = {}
        doc["PublisherInfo"] = [IPFInformationJson(
            ipfinfo).toJson() for ipfinfo in self.data.ipfinfo]
        doc["StorageService"] = []
        doc["ComputingService"] = []
        doc["LoginService"] = []
        doc["InformationService"] = []
        doc["Endpoint"] = []
        for serv in self.data.services:
            if serv is not None:
                endpoint = Endpoint()
                endpoint.URL = serv.Endpoint
                endpoint.InterfaceName = serv.Type
                endpoint.InterfaceVersion = serv.Version
                endpoint.Name = serv.Name
                endpointhash = ''
                if (serv.Endpoint != ''):
                    endpointhashobject = hashlib.md5(str(serv.Endpoint).encode('utf-8'))
                    endpointhash = "-"+endpointhashobject.hexdigest()
                endpoint.ID = "urn:ogf:glue2:xsede.org:Endpoint:%s-%s-%s%s" % (
                    serv.Version, serv.Name, serv.resource_name, endpointhash)
                endpoint.ServiceID = serv.ID
                endpoint.QualityLevel = serv.QualityLevel
                serv.EndpointID = endpoint.ID
                if serv.ServiceType not in doc:
                    doc[serv.ServiceType] = []
                doc[serv.ServiceType].append(
                    AbstractServiceOgfJson(serv).toJson())
                doc["Endpoint"].append(EndpointOgfJson(endpoint).toJson())
        return doc
