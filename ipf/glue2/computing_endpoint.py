
###############################################################################
#   Copyright 2012-2013 The University of Texas at Austin                     #
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

import datetime
import json
import time
from xml.dom.minidom import getDOMImplementation
import ConfigParser

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.sysinfo import ResourceName

from ipf.glue2.endpoint import *
from ipf.glue2.step import GlueStep

#######################################################################################################################

class ComputingEndpointStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step produces one or more documents containing one or more GLUE 2 ComputingEndpoint."
        self.time_out = 10
        self.requires = [ResourceName]
        self.produces = [ComputingEndpoint]

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name

        endpoints = self._run()

        for i in range(0,len(endpoints)):
            if endpoints[i].Name == None:
                endpoints[i].Name = "endpoint-%d" % (i+1)
        for endpoint in endpoints:
            endpoint.id = "%s.%s" % (endpoint.Name,self.resource_name)
            endpoint.ID = "urn:glue2:ComputingEndpoint:%s.%s" % (endpoint.Name,self.resource_name)
            endpoint.ServiceID = "urn:glue2:ComputingService:%s" % (self.resource_name)

            self._output(endpoint)

    def _run(self):
        raise StepError("ComputingEndpointStep._run not overriden")

#######################################################################################################################

class ParamComputingEndpointStep(ComputingEndpointStep):
    def __init__(self):
        ComputingEndpointStep.__init__(self)

        self.description = "create a ComputingEndpoint using parameters"
        self._acceptParameter("endpoint",
                              "An endpoint, represented as a dictionary. See ComputingEndpoint.fromJson() for the keys and values.",
                              True)

    def _run(self):
        try:
            endpoint_doc = self.params["endpoint"]
        except KeyError:
            raise StepError("endpoint not specified")
        endpoint = ComputingEndpoint()
        self.fromJson(endpoint, endpoint_doc)
        return [endpoint]

    def fromJson(self, endpoint, doc):
        # Entity
        self.Name = doc.get("Name")
        self.OtherInfo = doc.get("OtherInfo",[])
        self.Extension = doc.get("Extension",{})
                        
        # Endpoint
        self.URL = doc.get("URL")
        self.Capability = doc.get("Capability",[])
        self.Technology = doc.get("Technology")
        self.InterfaceName = doc.get("InterfaceName")
        self.InterfaceVersion = doc.get("InterfaceVersion")
        self.InterfaceExtension = doc.get("InterfaceExtension",[])
        self.WSDL = doc.get("WSDL",[])
        self.SupportedProfile = doc.get("SupportedProfile",[])
        self.Semantics = doc.get("Semantics",[])
        self.Implementor = doc.get("Implementor")
        self.ImplementationName = doc.get("ImplementationName")
        self.ImplementationVersion = doc.get("ImplementationVersion")
        self.QualityLevel = doc.get("QualityLevel")
        self.HealthState = doc.get("HealthState")
        self.HealthStateInfo = doc.get("HealthStateInfo")
        self.StartTime = textToDateTime(doc.get("StartTime"))
        self.IssuerCA = doc.get("IssuerCA")
        self.TrustedCA = doc.get("TrustedCA",[])
        self.DowntimeAnnounce = textToDateTime(doc.get("DowntimeAnnounce"))
        self.DowntimeStart = textToDateTime(doc.get("DowntimeStart"))
        self.DowntimeEnd = textToDateTime(doc.get("DowntimeEnd"))
        self.DowntimeInfo = doc.get("DowntimeInfo")

#######################################################################################################################

class NoComputingEndpointsStep(ComputingEndpointStep):
    def __init__(self):
        ComputingEndpointStep.__init__(self)

        self.description = "create no ComputingEndpoints"

    def _run(self):
        return []

#######################################################################################################################

class ComputingEndpoint(Endpoint):

    DEFAULT_VALIDITY = 3600 # seconds

    def __init__(self):
        Endpoint.__init__(self)

        self.Staging = None            # string (Staging)
        self.JobDescription = []       # list of string (JobDescription)
        self.TotalJobs = None          # integer
        self.RunningJobs = None        # integer
        self.WaitingJobs = None        # integer
        self.StagingJobs = None        # integer
        self.SuspendedJobs = None      # integer
        self.PreLRMSWaitingJobs = None # integer
        # use Service, Share, Activity in Endpoint
        #   instead of ComputingService, ComputingShare, ComputingActivity, ComputingEndpoint

#######################################################################################################################

class ComputingEndpointTeraGridXml(EndpointTeraGridXml):
    data_cls = ComputingEndpoint

    def __init__(self, data):
        EndpointTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingEndpoint")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        EndpointTeraGridXml.addToDomElement(self,doc,element)

        if self.data.Staging is not None:
            e = doc.createElement("Staging")
            e.appendChild(doc.createTextNode(self.data.Staging))
            element.appendChild(e)
        for description in self.data.JobDescription:
            e = doc.createElement("JobDescription")
            e.appendChild(doc.createTextNode(description))
            element.appendChild(e)
        if self.data.TotalJobs is not None:
            e = doc.createElement("TotalJobs")
            e.appendChild(doc.createTextNode(str(self.data.TotalJobs)))
            element.appendChild(e)
        if self.data.RunningJobs is not None:
            e = doc.createElement("RunningJobs")
            e.appendChild(doc.createTextNode(str(self.data.RunningJobs)))
            element.appendChild(e)
        if self.data.WaitingJobs is not None:
            e = doc.createElement("WaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.WaitingJobs)))
            element.appendChild(e)
        if self.data.StagingJobs is not None:
            e = doc.createElement("StagingJobs")
            e.appendChild(doc.createTextNode(str(self.data.StagingJobs)))
            element.appendChild(e)
        if self.data.SuspendedJobs is not None:
            e = doc.createElement("SuspendedJobs")
            e.appendChild(doc.createTextNode(str(self.data.SuspendedJobs)))
            element.appendChild(e)
        if self.data.PreLRMSWaitingJobs is not None:
            e = doc.createElement("PreLRMSWaitingJobs")
            e.appendChild(doc.createTextNode(str(self.data.PreLRMSWaitingJobs)))
            element.appendChild(e)
        if self.data.ServiceID is not None:
            e = doc.createElement("ComputingService")
            e.appendChild(doc.createTextNode(self.data.ServiceID))
            element.appendChild(e)
        for share in self.data.ShareID:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            element.appendChild(e)
        for activity in self.data.ActivityID:
            e = doc.createElement("ComputingActivity")
            e.appendChild(doc.createTextNode(activity))
            element.appendChild(e)

        return doc

#######################################################################################################################

class ComputingEndpointOgfJson(EndpointOgfJson):
    data_cls = ComputingEndpoint

    def __init__(self, data):
        EndpointOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EndpointOgfJson.toJson(self)

        if self.data.Staging is not None:
            doc["Staging"] = self.data.Staging
        if len(self.data.JobDescription) > 0:
            doc["JobDescription"] = self.data.JobDescription
        if self.data.TotalJobs is not None:
            doc["TotalJobs"] = self.data.TotalJobs
        if self.data.RunningJobs is not None:
            doc["RunningJobs"] = self.data.RunningJobs
        if self.data.WaitingJobs is not None:
            doc["WaitingJobs"] = self.data.WaitingJobs
        if self.data.StagingJobs is not None:
            doc["StagingJobs"] = self.data.StagingJobs
        if self.data.SuspendedJobs is not None:
            doc["SuspendedJobs"] = self.data.SuspendedJobs
        if self.data.PreLRMSWaitingJobs is not None:
            doc["PreLRMSWaitingJobs"] = self.data.PreLRMSWaitingJobs

        return doc

#######################################################################################################################
