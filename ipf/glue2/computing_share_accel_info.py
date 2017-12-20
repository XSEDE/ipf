
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

class ComputingShareAcceleratorInfoStep(GlueStep):

    def __init__(self):
        GlueStep.__init__(self)

        self.description = "This step provides documents in the GLUE 2 ComputingShareAcceleratorInfo schema. For a batch scheduled system, this is typically that scheduler."
        self.time_out = 10
        #self.requires = [ResourceName,AcceleratorEnvironments,ComputingShares]
        self.requires = [ResourceName,AcceleratorEnvironments,ComputingShares]
        self.produces = [ComputingShareAcceleratorInfo]

        self.resource_name = None
        self.accel_envs = None
        self.manager = None
        self.share_accel_info = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self.accel_envs = self._getInput(AcceleratorEnvironments).accel_envs
        #self.manager = self._getInput(ComputingManager).manager
        self.shares = self._getInput(ComputingShares).shares
        self.ComputingManagerID = "urn:glue2:ComputingManager:%s" % (self.resource_name)
        #self.UsedAcceleratorSlots = None         # integer

        share_accel_info = self._run()

        share_accel_info.id = "%s" % (self.resource_name)
        share_accel_info.ID = "urn:glue2:ComputingShareAcceleratorInfo:%s" % (self.resource_name)

        for accel_env in self.accel_envs:
            share_accel_info._addAcceleratorEnvironment(accel_env)
        #if share_accel_info.UsedAcceleratorSlots is not None:
        #    if share_accel_info.TotalPhysicalAccelerators is not None:
        #        self.debug("TotalPhysicalAccelerators "+str(share_accel_info.TotalPhysicalAccelerators))
        #        if share_accel_info.FreeAcceleratorSlots == None:
        #            share_accel_info.FreeAcceleratorSlots = 0
        #        share_accel_info.FreeAcceleratorSlots = share_accel_info.TotalPhysicalAccelerators - share_accel_info.UsedAcceleratorSlots    
        if share_accel_info.UsedAcceleratorSlots is not None:
            if share_accel_info.TotalAcceleratorSlots is not None:
                if share_accel_info.FreeAcceleratorSlots == None:
                    share_accel_info.FreeAcceleratorSlots = 0
                share_accel_info.FreeAcceleratorSlots = share_accel_info.TotalAcceleratorSlots - share_accel_info.UsedAcceleratorSlots    
        #share_accel_info._addComputingShares(self.shares)
        #kkshare_accel_info._addComputingShare(self.share)
        #for share in self.shares:
        #    share_accel_info._addComputingShare(share)

        self._output(share_accel_info)

#######################################################################################################################

class ComputingShareAcceleratorInfo(Entity):
    def __init__(self):
        Entity.__init__(self)
        
        self.Type = None            # integer
        self.FreeAcceleratorSlots = None                   # integer
        self.UsedAcceleratorSlots = None         # integer
        self.MaxAcceleratorSlotsPerJob = None         # integer
        self.TotalPhysicalAccelerators = None           # integer
        self.TotalLogicalAccelerators = None           # integer
        self.TotalAcceleratorSlots = None                   # integer
        # use Service and Resource of Manager instead of ComputingService and ExecutionEnvironment
        self.ComputingShareID = []       # list of string (LocalID)


    def _addAcceleratorEnvironment(self, accel_env):
        #self.ResourceID.append(accel_env.ID)
        if accel_env.PhysicalAccelerators is not None:
            if self.TotalPhysicalAccelerators == None:
                self.TotalPhysicalAccelerators = 0
            self.TotalPhysicalAccelerators = self.TotalPhysicalAccelerators + accel_env.PhysicalAccelerators
            if self.TotalAcceleratorSlots == None:
                self.TotalAcceleratorSlots = 0
            self.TotalAcceleratorSlots = self.TotalAcceleratorSlots + accel_env.TotalAcceleratorSlots
            #self.TotalPhysicalAccelerators = self.TotalPhysicalAccelerators + accel_env.TotalInstances * accel_env.PhysicalAccelerators
            #if self.TotalLogicalAccelerators == None:
            #    self.TotalLogicalAccelerators = 0
            #self.TotalLogicalAcclerators = self.TotalLogicalAccelerators + accel_env.TotalInstances * accel_env.LogicalAccelerators
            #self.TotalSlots = self.TotalLogicalAccelerators
        if accel_env.UsedAcceleratorSlots is not None:
            if self.UsedAcceleratorSlots == None:
                self.UsedAcceleratorSlots = 0
            self.UsedAcceleratorSlots = self.UsedAcceleratorSlots + accel_env.UsedAcceleratorSlots
        if self.Type == None:
            if accel_env.Type is not None:
                self.Type = accel_env.Type
        


    def _addComputingShares(self, shares):
        self.ComputingShareID = []
        if len(shares) == 0:
            return
        for share in shares:
            self.ComputingShareID.append(share.ID)

    def _addComputingShare(self, share):
        if self.UsedAcceleratorSlots == None:
            self.UsedAcceleratorSlots = 0
        self.UsedAcceleratorSlots = self.UsedAcceleratorSlots + share.UsedSlots



#######################################################################################################################

class ComputingShareAcceleratorInfoOgfJson(EntityOgfJson):
    data_cls = ComputingShareAcceleratorInfo

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        if self.data.Type is not None:
            doc["Type"] = self.data.Type
        if self.data.FreeAcceleratorSlots is not None:
            doc["FreeAcceleratorSlots"] = self.data.FreeAcceleratorSlots
        if self.data.UsedAcceleratorSlots is not None:
            doc["UsedAcceleratorSlots"] = self.data.UsedAcceleratorSlots

        if len(self.data.ComputingShareID) > 0:
            doc["Associations"]["ComputingShareID"] = self.data.ComputingShareID

        return doc

#######################################################################################################################
