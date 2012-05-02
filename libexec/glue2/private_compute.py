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

class PrivateComputeStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "glue2/teragrid/private_compute"
        self.description = "creates a single document containing all sensitive compute-related information"
        self.time_out = 5
        self.requires_types = ["ipf/resource_name.txt",
                               "ipf/site_name.txt",
                               "glue2/teragrid/computing_activities.json"]
        self.produces_types = ["glue2/teragrid/private_compute.xml",
                               "glue2/teragrid/private_compute.json"]

        self.more_inputs = True

        self.private_compute = PrivateCompute()

    def input(self, document):
        if document.type == "ipf/resource_name.txt":
            self.private_compute.resource_name = document.body.rstrip()
        elif document.type == "ipf/site_name.txt":
            self.private_computesite_name = document.body.rstrip()
        elif document.type == "glue2/teragrid/computing_activities.json":
            try:
                self.private_compute.activities = document.activities
            except AttributeError:
                self.private_compute.activities = self._parseActivitiesJson(document.body)
        else:
            self.info("ignoring unwanted input "+document.type)

    def _parseActivitiesJson(self, body):
        doc = json.loads(body)
        activities = []
        for activity_dict in doc:
            activity = ComputingActivity()
            activity.fromJson(activity_dict)
            activities.append(activity)
        return activities

    def run(self):
        self.info("waiting for all inputs")
        while self.more_inputs:
            time.sleep(0.25)

        if "glue2/teragrid/private_compute.xml" in self.requested_types:
            self.engine.output(self,PrivateComputeDocumentXml(self.private_compute))
        if "glue2/teragrid/private_compute.json" in self.requested_types:
            self.engine.output(self,PrivateComputeDocumentJson(self.private_compute))

    def noMoreInputs(self):
        self.more_inputs = False

#######################################################################################################################

class PrivateCompute(object):
    def __init__(self):
        self.resource_name = None
        self.site_name = None
        self.activities = None

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

        if self.activities is not None:
            for activity in self.activities:
                root.appendChild(activity.toDom().documentElement.firstChild)

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
            doc["ComputingActivities"] = self.activities
        
        return doc

    ###################################################################################################################

    def fromJson(self, doc):
        self.resource_name = doc.get("ResourceID")
        self.site_name = doc.get("SiteID")
        self.activities = doc.get("ComputingActivities",[])


#######################################################################################################################

if __name__ == "__main__":
    StepEngine(PrivateComputeStep())
