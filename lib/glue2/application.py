
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

        doc["AppName"] = env.AppName
        if env.AppVersion is not None:
            doc["AppVersion"] = env.AppVersion
        if env.Repository is not None:
            doc["Repository"] = env.Repository
        if env.State is not None:
            doc["State"] = env.State
        if env.RemovalDate is not None:
            doc["RemovalDate"] = dateTimeToText(env.RemovalDate)
        if env.License is not None:
            doc["License"] = env.License
        if env.Description is not None:
            doc["Description"] = env.Description
        if len(env.BestBenchmark) > 0:
            doc["BestBenchmark"] = env.BestBenchmark
        if env.ParallelSupport is not None:
            doc["ParallelSupport"] = env.ParallelSupport
        if env.MaxSlots is not None:
            doc["MaxSlots"] = env.MaxSlots
        if env.MaxJobs is not None:
            doc["MaxJobs"] = env.MaxJobs
        if env.MaxUserSeats is not None:
            doc["MaxUserSeats"] = env.MaxUserSeats
        if env.FreeSlots is not None:
            doc["FreeSlots"] = env.FreeSlots
        if env.FreeJobs is not None:
            doc["FreeJobs"] = env.FreeJobs
        if env.FreeUserSeats is not None:
            doc["FreeUserSeats"] = env.FreeUserSeats

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
    data_cls = ApplicationEnvironment

    def __init__(self, data):
        EntityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = EntityOgfJson.toJson(self)
        
        doc["Type"] = handle.Type
        doc["Value"] = handle.Value
        doc["ApplicationEnvironment"] = handle.ApplicationEnvironment

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
            doc["ApplicationEnvironment"].append(ApplicationEnvironmentOgfJson.toJson(env))
        doc["ApplicationHandle"] = []
        for handle in self.data.handles:
            doc["ApplicationHandle"].append(ApplicationHandleOgfJson.toJson(handle))
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
