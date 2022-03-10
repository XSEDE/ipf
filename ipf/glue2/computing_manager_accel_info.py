
###############################################################################
#   Copyright 2011-2013 The University of Texas at Austin                     #
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
from ipf.sysinfo import ResourceName

from .computing_share import ComputingShares
#from .computing_manager import ComputingManager
from .accelerator_environment import AcceleratorEnvironments
from .entity import *
#from .manager import *
from .step import GlueStep

#######################################################################################################################


class ComputingManagerAcceleratorInfoStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step provides documents in the GLUE 2 ComputingManagerAcceleratorInfo schema. For a batch scheduled system, this is typically that scheduler."
        self.time_out = 10
        #self.requires = [ResourceName,AcceleratorEnvironments,ComputingManager]
        #self.requires = [ResourceName,AcceleratorEnvironments,ComputingShares]
        self.requires = [ResourceName, AcceleratorEnvironments]
        self.produces = [ComputingManagerAcceleratorInfo]

        self.resource_name = None
        self.accel_envs = None
        self.manager = None
        self.manager_accel_info = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.accel_envs = self._getInput(AcceleratorEnvironments).accel_envs
        #self.manager = self._getInput(ComputingManager).manager
        #self.shares = self._getInput(ComputingShares).shares

        manager_accel_info = self._run()
        manager_accel_info.ComputingManagerID = "urn:ogf:glue2:xsede.org:ComputingManager:%s" % (
            self.resource_name)

        manager_accel_info.id = "%s" % (self.resource_name)
        manager_accel_info.ID = "urn:ogf:glue2:xsede.org:ComputingManagerAcceleratorInfo:%s" % (
            self.resource_name)

        if self.accel_envs:
            for accel_env in self.accel_envs:
                manager_accel_info._addAcceleratorEnvironment(accel_env)
        # for share in self.shares:
        #    manager_accel_info._addComputingShare(share)

        self._output(manager_accel_info)

#######################################################################################################################


class ComputingManagerAcceleratorInfo(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.TotalPhysicalAccelerators = None            # integer
        self.TotalLogicalAccelerators = None            # integer
        self.TotalAcceleratorSlots = None                   # integer
        self.UsedAcceleratorSlots = None         # integer
        # use Service and Resource of Manager instead of ComputingService and ExecutionEnvironment
        self.ComputingManagerID = []       # list of string (LocalID)

    def _addAcceleratorEnvironment(self, accel_env):
        # self.ResourceID.append(accel_env.ID)
        if accel_env.PhysicalAccelerators is not None:
            if self.TotalPhysicalAccelerators == None:
                self.TotalPhysicalAccelerators = 0
            self.TotalPhysicalAccelerators = self.TotalPhysicalAccelerators + \
                accel_env.TotalInstances * accel_env.PhysicalAccelerators
        if accel_env.LogicalAccelerators is not None:
            if self.TotalLogicalAccelerators == None:
                self.TotalLogicalAccelerators = 0
            self.TotalLogicalAccelerators = self.TotalLogicalAccelerators + \
                accel_env.TotalInstances * accel_env.LogicalAccelerators
            self.TotalSlots = self.TotalLogicalAccelerators
        if accel_env.UsedAcceleratorSlots is not None:
            if self.UsedAcceleratorSlots == None:
                self.UsedAcceleratorSlots = 0
            self.UsedAcceleratorSlots = self.UsedAcceleratorSlots + \
                accel_env.UsedAcceleratorSlots

    def _addComputingShare(self, share):
        if self.UsedAcceleratorSlots == None:
            self.UsedAcceleratorSlots = 0
        self.UsedAcceleratorSlots = self.UsedAcceleratorSlots + share.UsedSlots

#######################################################################################################################


class ComputingManagerAcceleratorInfoOgfJson(EntityOgfJson):
    data_cls = ComputingManagerAcceleratorInfo

    def __init__(self, data):
        EntityOgfJson.__init__(self, data)

    def get(self):
        return json.dumps(self.toJson(), sort_keys=True, indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.TotalPhysicalAccelerators is not None:
            doc["TotalPhysicalAccelerators"] = self.data.TotalPhysicalAccelerators
        if self.data.TotalLogicalAccelerators is not None:
            doc["TotalLogicalAccelerators"] = self.data.TotalLogicalAccelerators
        if self.data.UsedAcceleratorSlots is not None:
            doc["UsedAcceleratorSlots"] = self.data.UsedAcceleratorSlots

        if len(self.data.ComputingManagerID) > 0:
            doc["Associations"] = {}
            doc["Associations"]["ComputingManagerID"] = self.data.ComputingManagerID
        if self.data.TotalPhysicalAccelerators is not None:
            return doc
        else:
            return

#######################################################################################################################
