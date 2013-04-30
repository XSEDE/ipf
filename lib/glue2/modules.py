
###############################################################################
#   Copyright 2013 The University of Texas at Austin                          #
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
import glue2.application
from glue2.types import AppEnvState,ApplicationHandle

#######################################################################################################################

class LModApplicationsStep(glue2.application.ApplicationsStep):
    def __init__(self):
        glue2.application.ApplicationsStep.__init__(self)

        self._acceptParameter("exclude","a comma-separated list of modules to ignore (default is to ignore none)",
                              False)

    def _run(self):
        try:
            self.exclude = self.params["exclude"].split(",")
        except KeyError:
            self.exclude = []

        apps = glue2.application.Applications(self.resource_name)

        module_paths = []
        try:
            #paths = os.environ["LMOD_DEFAULT_MODULEPATH"]
            paths = os.environ["MODULEPATH"]
            module_paths.extend(paths.split(":"))
        except KeyError:
            raise StepError("didn't find environment variable LMOD_DEFAULT_MODULEPATH")

        apps = glue2.application.Applications(self.resource_name)
        for path in module_paths:
            try:
                packages = os.listdir(path)
            except OSError:
                continue
            for name in packages:
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
                        self._addModule(os.path.join(path,name,file_name),name,file_name,apps)
        return apps
    
    def _addModule(self, path, name, version, apps):
        env = glue2.application.ApplicationEnvironment()
        env.AppName = name
        env.AppVersion = version

        file = open(path)
        text = file.read()
        file.close()

        m = re.search("\"Description: ([^\"]+)\"",text)
        if m is not None:
            env.Description = m.group(1)
        else:
            self.debug("no description in "+path)
        m = re.search("\"URL: ([^\"]+)\"",text)
        if m is not None:
            env.Repository = m.group(1)
        else:
            self.debug("no URL in "+path)

        handle = glue2.application.ApplicationHandle()
        handle.Type = ApplicationHandle.MODULE
        handle.Value = name+"/"+version

        apps.add(env,[handle])

#######################################################################################################################
