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
from ipf.error import StepError
from ipf.step import Step

#######################################################################################################################

class PrivateComputeStep(Step):
    name = "glue2/teragrid/private_compute"
    description = "creates a single document containing all sensitive compute-related information"
    time_out = 5
    requires_types = ["ipf/resource_name.txt",
                      "ipf/site_name.txt",
                      "glue2/teragrid/computing_activities.json"]
    produces_types = ["glue2/teragrid/private_compute.xml",
                      "glue2/teragrid/private_compute.json"]

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")
        sn_doc = self._getInput("ipf/site_name.txt")
        activities_doc = self._getInput("glue2/teragrid/computing_activities.json")

        private_compute = PrivateCompute()
        private_compute.resource_name = rn_doc.resource_name
        private_compute.site_name = sn_doc.site_name
        private_compute.activities = activities_doc.activities
        private_compute.hide = activities_doc.hide
        
        if "glue2/teragrid/private_compute.xml" in self.requested_types:
            self.output_queue.put(PrivateComputeDocumentXml(private_compute))
        if "glue2/teragrid/private_compute.json" in self.requested_types:
            self.output_queue.put(PrivateComputeDocumentJson(private_compute))

#######################################################################################################################

class PrivateCompute(object):
    def __init__(self):
        self.resource_name = None
        self.site_name = None
        self.activities = None
        self.hide = []

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

        if self.activities is not None:
            for activity in self.activities:
                root.appendChild(activity.toDom(self.hide).documentElement.firstChild)

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

        if self.activities is not None:
            docs = []
            for activity in self.activities:
                docs.append(activity.toJson(self.hide))
            doc["ComputingActivities"] = docs
        
        return doc

    ###################################################################################################################

    def fromJson(self, doc):
        self.resource_name = doc.get("ResourceID")
        self.site_name = doc.get("SiteID")
        self.activities = doc.get("ComputingActivities",[])


#######################################################################################################################

class PrivateComputeDocumentXml(Document):
    def __init__(self, private_compute):
        Document.__init__(self, private_compute.resource_name, "glue2/teragrid/private_compute.xml")
        self.private_compute = private_compute

    def _setBody(self, body):
        raise DocumentError("PrivateComputeDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        return self.private_compute.toDom().toxml()

#######################################################################################################################

class PrivateComputeDocumentJson(Document):
    def __init__(self, private_compute):
        Document.__init__(self, private_compute.resource_name, "glue2/teragrid/private_compute.json")
        self.private_compute = private_compute

    def _setBody(self, body):
        self.private_compute = PrivateCompute()
        self.private_compute.fromJson(json.loads(body))

    def _getBody(self):
        return json.dumps(self.private_compute.toJson(),indent=4)

#######################################################################################################################
