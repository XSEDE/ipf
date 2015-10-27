
###############################################################################
#   Copyright 2013-2014 The University of Texas at Austin                     #
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

import commands
import os
import re

from ipf.error import StepError
from . import application
from . import service
#from . import endpoint
#from .step import GlueStep
#from .step import computing_service
from .types import AppEnvState,ApplicationHandle
from . import computing_activity
from . import computing_manager
from . import computing_service
from . import computing_share
from . import execution_environment

#######################################################################################################################
class InstalledServiceStep(computing_service.ComputingServiceStep):
    def __init__(self):
        computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = computing_service.ComputingService()
        #service.Name = "PBS"
        #service.Capability = ["executionmanagement.jobexecution",
        #                      "executionmanagement.jobdescription",
        #                      "executionmanagement.jobmanager",
        #                      "executionmanagement.executionandplanning",
        #                      "executionmanagement.reservation",
        #                      ]
        #service.Type = "ipf.PBS"
        #service.QualityLevel = "production"

        module_paths = []
        try:
            paths = os.environ["SERVICEPATH"]
            module_paths.extend(paths.split(":"))
        except KeyError:
            raise StepError("didn't find environment variable SERVICEPATH")

        for path in module_paths:
            try:
                packages = os.listdir(path)
            except OSError:
                continue
            for name in packages:
                print("name of package is" +name)
                if name.startswith("."):
                    continue
                if not os.path.isdir(os.path.join(path,name)):
                    # assume these are modules that just import other modules
                    continue
                for file_name in os.listdir(os.path.join(path,name)):
                    if file_name.startswith("."):
                        continue
                    if file_name.endswith("~"):
                        continue
                    if file_name.endswith(".lua"):
                        self._addModule(os.path.join(path,name,file_name),name,file_name[:len(file_name)-4],apps)
                    else:
                        self.info("calling addmodule w/ version")
                        self._addModule(os.path.join(path,name,file_name),name,file_name,service)

        return service

    
    def _addModule(self, path, name, version, service):
        env = application.ApplicationEnvironment()
        #env.AppName = name
        #env.AppVersion = version

        try:
            file = open(path)
        except IOError, e:
            self.warning("%s" % e)
            return
        text = file.read()
        file.close()
	print("in correct _addModule")
        m = re.search("\"Description:([^\"]+)\"",text)
        if m is not None:
            env.Description = m.group(1).strip()
        else:
            self.debug("no description in "+path)
            print("no description in "+path)
        m = re.search("\"URL:([^\"]+)\"",text)
        if m is not None:
            env.Repository = m.group(1).strip()
        else:
            self.debug("no URL in "+path)
        m = re.search("\"Category:([^\"]+)\"",text)
        if m is not None:
            env.Extension["Category"] = map(str.strip,m.group(1).split(","))
	    print(" python is silly")
		
        else:
            self.debug("no Category in "+path)
        m = re.search("\"Keywords:([^\"]+)\"",text)
        if m is not None:
	    env.Keywords = map(str.strip,m.group(1).split(","))
        else:
            self.debug("no Keywords in "+path)
        m = re.search("\"SupportStatus:([^\"]+)\"",text)
        if m is not None:
	    supportstatus = []
	    supportstatus.append(map(str.strip,m.group(1).split(",")))
            env.Extension["SupportStatus"] = m.group(1).strip()
        else:
            self.debug("no SupportStatus in "+path)

        handle = application.ApplicationHandle()
        handle.Type = ApplicationHandle.MODULE
        handle.Value = name+"/"+version

        apps.add(env,[handle])

#######################################################################################################################

class ComputingServiceXsedeJson(ServiceOgfJson):
    data_cls = ComputingService

    def __init__(self, data):
        ServiceOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        doc = ServiceOgfJson.toJson(self)

        if self.data.Type is not None:
            doc["Type"] = self.data.Type
        if self.data.Capability is not None:
            doc["Capability"] = self.data.Capability
        if self.data.QualityLevel is not None:
            doc["QualityLevel"] = self.data.QualityLevel
        if self.data.Name is not None:
            doc["Name"] = self.data.Name

        return doc

#######################################################################################################################
