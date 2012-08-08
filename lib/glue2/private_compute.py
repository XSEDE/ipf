
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
from ipf.error import StepError
from ipf.name import ResourceName
from ipf.name import SiteName
from ipf.step import Step

from glue2.computing_activity import ComputingActivities, ComputingActivityTeraGridXml, ComputingActivityIpfJson

#######################################################################################################################

class PrivateComputeStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "creates a single data containing all sensitive compute-related information"
        self.time_out = 5
        self.requires = [ResourceName,SiteName,ComputingActivities]
        self.produces = [PrivateCompute]

    def run(self):
        private_compute = PrivateCompute()
        private_compute.resource_name = self._getInput(ResourceName).resource_name
        private_compute.site_name = self._getInput(SiteName).site_name
        private_compute.activities = self._getInput(ComputingActivities).activities
        private_compute.id = private_compute.resource_name
        
        self._output(private_compute)

#######################################################################################################################

class PrivateCompute(Data):
    def __init__(self):
        Data.__init__(self)

        self.resource_name = None
        self.site_name = None
        self.activities = []

    def fromJson(self, doc):
        self.resource_name = doc.get("ResourceID")
        self.site_name = doc.get("SiteID")
        self.activities = doc.get("ComputingActivities",[])

#######################################################################################################################

class PrivateComputeTeraGridXml(Representation):
    data_cls = PrivateCompute

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(private_compute):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "glue2",None)

        if private_compute.resource_name is None:
            raise StepError("resource name is not set")
        e = doc.createElement("ResourceID")
        e.appendChild(doc.createTextNode(private_compute.resource_name))
        doc.documentElement.appendChild(e)

        if private_compute.site_name is None:
            raise StepError("site name is not set")
        e = doc.createElement("SiteID")
        e.appendChild(doc.createTextNode(private_compute.site_name))
        doc.documentElement.appendChild(e)

        root = doc.createElement("Entities")
        doc.documentElement.appendChild(root)

        for activity in private_compute.activities:
            root.appendChild(ComputingActivityTeraGridXml.toDom(activity).documentElement.firstChild)
        return doc


#######################################################################################################################

class PrivateComputeIpfJson(Representation):
    data_cls = PrivateCompute

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),indent=4)

    @staticmethod
    def toJson(private_compute):
        doc = {}

        if private_compute.resource_name is None:
            raise StepError("resource name is not set")
        doc["ResourceID"] = private_compute.resource_name
        if private_compute.site_name is None:
            raise StepError("site name is not set")
        doc["SiteID"] = private_compute.site_name

        if len(private_compute.activities) > 0:
            docs = []
            for activity in private_compute.activities:
                docs.append(ComputingActivityIpfJson.toJson(activity))
            doc["ComputingActivities"] = docs
        
        return doc

#######################################################################################################################
