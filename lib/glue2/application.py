
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

import json

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.step import Step
from ipf.sysinfo import ResourceName

from glue2.entity import *

#######################################################################################################################

class ApplicationEnvironment(Entity):

    def __init__(self):
        Entity.__init__(self)

        self.AppName = "unknown"       # string
        self.AppVersion = None         # string
        self.Repository = None         # string (url)
        self.State = None              # string (AppEnvState_t)
        self.RemovalDate = None        # datetime
        self.License = None            # string (License_t)
        self.Description = None        # string
        self.BestBenchmark = []        # string (ID of Benchmark)
        self.ParallelSupport = None    # string (ParallelSupport_t)
        self.MaxSlots = None           # integer
        self.MaxJobs = None            # integer
        self.MaxUserSeats = None       # integer
        self.FreeSlots = None          # integer
        self.FreeJobs = None           # integer
        self.FreeUserSeats = None      # integer
        self.ExecutionEnvironment = [] # string (ID)
        self.ComputingManager = None   # string (ID)
        self.ApplicationHandle = []    # string (ID)
        
    def __str__(self):
        return json.dumps(ApplicationEnvironmentOgfJson.toJson(self),sort_keys=True,indent=4)

#######################################################################################################################

class ApplicationEnvironmentOgfJson(EntityOgfJson):
    data_cls = ApplicationEnvironment

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)

        doc["AppName"] = self.data.AppName
        if self.data.AppVersion is not None:
            doc["AppVersion"] = self.data.AppVersion
        if self.data.Repository is not None:
            doc["Repository"] = self.data.Repository
        if self.data.State is not None:
            doc["State"] = self.data.State
        if self.data.RemovalDate is not None:
            doc["RemovalDate"] = dateTimeToText(self.data.RemovalDate)
        if self.data.License is not None:
            doc["License"] = self.data.License
        if self.data.Description is not None:
            doc["Description"] = self.data.Description
        if len(self.data.BestBenchmark) > 0:
            doc["BestBenchmark"] = self.data.BestBenchmark
        if self.data.ParallelSupport is not None:
            doc["ParallelSupport"] = self.data.ParallelSupport
        if self.data.MaxSlots is not None:
            doc["MaxSlots"] = self.data.MaxSlots
        if self.data.MaxJobs is not None:
            doc["MaxJobs"] = self.data.MaxJobs
        if self.data.MaxUserSeats is not None:
            doc["MaxUserSeats"] = self.data.MaxUserSeats
        if self.data.FreeSlots is not None:
            doc["FreeSlots"] = self.data.FreeSlots
        if self.data.FreeJobs is not None:
            doc["FreeJobs"] = self.data.FreeJobs
        if self.data.FreeUserSeats is not None:
            doc["FreeUserSeats"] = self.data.FreeUserSeats

        return doc

#######################################################################################################################

class ApplicationHandle(Entity):
    def __init__(self):
        Entity.__init__(self)

        self.Type = "unknown"               # string (ApplicationHandle_t)
        self.Value = "unknown"              # string
        self.ApplicationEnvironment = None  # string (ID)

#######################################################################################################################

class ApplicationHandleOgfJson(EntityOgfJson):
    data_cls = ApplicationHandle

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)
        
        doc["Type"] = self.data.Type
        doc["Value"] = self.data.Value
        doc["ApplicationEnvironment"] = self.data.ApplicationEnvironment

        return doc
    
#######################################################################################################################
    
class Applications(Data):
    def __init__(self, resource_name):
        Data.__init__(self)
        self.id = resource_name
        self.environments = []
        self.handles = []
        self.resource_name = resource_name

    def add(self, env, handles):
        if env.AppVersion is None:
            app_version = "unknown"
        else:
            app_version = env.AppVersion
        env.Name = "%s-%s" % (env.AppName,app_version)
        env.id =  "%s.%s.%s" % (app_version,env.AppName,self.resource_name)
        env.ID = "urn:glue2:ApplicationEnvironment:%s.%s.%s" % (app_version,env.AppName,self.resource_name)

        env.ApplicationHandle = []
        for handle in handles:
            handle.ApplicationEnvironment = env.ID
            handle.Name = "%s-%s" % (env.AppName,app_version)
            handle.id =  "%s.%s.%s.%s" % (handle.Type,app_version,env.AppName,self.resource_name)
            handle.ID = "urn:glue2:ApplicationHandle:%s:%s.%s.%s" % \
                        (handle.Type,app_version,env.AppName,self.resource_name)
            env.ApplicationHandle.append(handle.ID)

        self.environments.append(env)
        self.handles.extend(handles)
    
#######################################################################################################################

class ApplicationsOgfJson(Representation):
    data_cls = Applications

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = {}
        doc["ApplicationEnvironment"] = []
        for env in self.data.environments:
            doc["ApplicationEnvironment"].append(ApplicationEnvironmentOgfJson(env).toJson())
        doc["ApplicationHandle"] = []
        for handle in self.data.handles:
            doc["ApplicationHandle"].append(ApplicationHandleOgfJson(handle).toJson())
        return doc

#######################################################################################################################

class ApplicationsStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces a document containing GLUE 2 ApplicationEnvironment and ApplicationHandle"
        self.time_out = 30
        self.requires = [ResourceName]
        self.produces = [Applications]

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        self._output(self._run())

    def _run(self):
        raise StepError("ApplicationsStep._run not overriden")

#######################################################################################################################
