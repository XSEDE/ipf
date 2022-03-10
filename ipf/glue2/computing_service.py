
###############################################################################
#   Copyright 2009-2014 The University of Texas at Austin                     #
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

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import NoMoreInputsError,StepError
from ipf.sysinfo import ResourceName

from .computing_activity import ComputingActivity, ComputingActivities
from .computing_share import ComputingShares
from .location import Location
from .service import *
from .step import GlueStep

#######################################################################################################################

class ComputingServiceStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step provides a GLUE 2 ComputingService document. It is an aggregation mechanism"
        self.time_out = 10
        self.requires = [ResourceName,Location,ComputingActivities,ComputingShares]
        self.produces = [ComputingService]

        self.resource_name = None
        self.location = None
        self.activities = None
        self.shares = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.location = self._getInput(Location).ID
        self.activities = self._getInput(ComputingActivities).activities
        self.shares = self._getInput(ComputingShares).shares

        service = self._run()

        service.id = self.resource_name
        service.ID = "urn:ogf:glue2:xsede.org:ComputingService:%s" % (self.resource_name)
        service.LocationID = self.location
        service.ManagerID = ["urn:ogf:glue2:xsede.org:ComputingManager:%s" % (self.resource_name)]


        service._addActivities(self.activities)
        service._addShares(self.shares)

        for share in self.shares:
            share.ServiceID = service.ID

        self._output(service)

    def _run(self):
        raise StepError("ComputingServiceStep._run not overriden")

#######################################################################################################################

class ComputingService(Service):
    def __init__(self):
        Service.__init__(self)

        self.TotalJobs = None          # integer
        self.RunningJobs = None        # integer
        self.WaitingJobs = None        # integer
        self.StagingJobs = None        # integer
        self.SuspendedJobs = None      # integer
        self.PreLRMSWaitingJobs = None # integer
        # use Endpoint, Share, Manager, Service in Service
        #   instead of ComputingEndpoint, ComputingShare, ComputingManager, and StorageService

    def _addActivities(self, activities):
        self.RunningJobs = 0
        self.WaitingJobs = 0
        self.StagingJobs = 0
        self.SuspendedJobs = 0
        self.PreLRMSWaitingJobs = 0
        for activity in activities:
            if activity.State[0] == ComputingActivity.STATE_RUNNING:
                self.RunningJobs = self.RunningJobs + 1
            elif activity.State[0] == ComputingActivity.STATE_PENDING:
                self.WaitingJobs = self.WaitingJobs + 1
            elif activity.State[0] == ComputingActivity.STATE_HELD:
                self.WaitingJobs = self.WaitingJobs + 1
            else:
                # output a warning
                pass
        self.TotalJobs = self.RunningJobs + self.WaitingJobs + self.StagingJobs + self.SuspendedJobs + \
                         self.PreLRMSWaitingJobs

    def _addShares(self, shares):
        self.ShareID = []
        if len(shares) == 0:
            return
        for share in shares:
            self.ShareID.append(share.ID)

#######################################################################################################################

class ComputingServiceTeraGridXml(ServiceTeraGridXml):
    data_cls = ComputingService

    def __init__(self, data):
        ServiceTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingService")
        doc.documentElement.appendChild(root)

        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        ServiceTeraGridXml.addToDomElement(self,doc,element)

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
        for id in self.data.ShareID:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for id in self.data.ManagerID:
            e = doc.createElement("ComputingManager")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)
        for id in self.data.ServiceID:
            e = doc.createElement("StorageService")
            e.appendChild(doc.createTextNode(id))
            element.appendChild(e)

#######################################################################################################################

class ComputingServiceOgfJson(ServiceOgfJson):
    data_cls = ComputingService

    def __init__(self, data):
        ServiceOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = ServiceOgfJson.toJson(self)

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
