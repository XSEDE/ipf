
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
from .types import AppEnvState,ApplicationHandle

#######################################################################################################################

class LModApplicationsStep(application.ApplicationsStep):
    def __init__(self):
        application.ApplicationsStep.__init__(self)

        self._acceptParameter("exclude","a comma-separated list of modules to ignore (default is to ignore none)",
                              False)

    def _run(self):
        try:
            self.exclude = self.params["exclude"].split(",")
        except KeyError:
            self.exclude = []

        apps = application.Applications(self.resource_name)

        module_paths = []
        try:
            paths = os.environ["MODULEPATH"]
            module_paths.extend(paths.split(":"))
        except KeyError:
            raise StepError("didn't find environment variable MODULEPATH")

        apps = application.Applications(self.resource_name)
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
        env = application.ApplicationEnvironment()
        env.AppName = name
        env.AppVersion = version

        try:
            file = open(path)
        except IOError, e:
            self.warning("%s" % e)
            return
        text = file.read()
        file.close()

        m = re.search("\"Description:([^\"]+)\"",text)
        if m is not None:
            env.Description = m.group(1).strip()
        else:
            self.debug("no description in "+path)
        m = re.search("\"URL:([^\"]+)\"",text)
        if m is not None:
            env.Repository = m.group(1).strip()
        else:
            self.debug("no URL in "+path)
        m = re.search("\"Category:([^\"]+)\"",text)
        if m is not None:
            env.Extension["Category"] = map(str.strip,m.group(1).split(","))
        else:
            self.debug("no Category in "+path)
        m = re.search("\"Keywords:([^\"]+)\"",text)
        if m is not None:
            env.Extension["Keywords"] = map(str.strip,m.group(1).split(","))
        else:
            self.debug("no Keywords in "+path)

        handle = application.ApplicationHandle()
        handle.Type = ApplicationHandle.MODULE
        handle.Value = name+"/"+version

        apps.add(env,[handle])

#######################################################################################################################

class ModulesApplicationsStep(application.ApplicationsStep):
    def __init__(self):
        application.ApplicationsStep.__init__(self)

        self._acceptParameter("exclude","a comma-separated list of modules to ignore (default is to ignore none)",
                              False)

    def _run(self):
        try:
            self.exclude = self.params["exclude"].split(",")
        except KeyError:
            self.exclude = []

        apps = application.Applications(self.resource_name)

        module_paths = []
        try:
            paths = os.environ["MODULEPATH"]
            module_paths.extend(paths.split(":"))
        except KeyError:
            raise StepError("didn't find environment variable MODULEPATH")

        for path in module_paths:
            self._addPath(path,path,module_paths,apps)

        return apps

    def _addPath(self, path, module_path, module_paths, apps):
        try:
            file_names = os.listdir(path)
        except OSError:
            return
        for name in file_names:
            if os.path.join(path,name) in module_paths:
                # don't visit other module paths
                continue
            if os.path.isdir(os.path.join(path,name)):
                self._addPath(os.path.join(path,name),module_path,module_paths,apps)
            else:
                self._addModule(os.path.join(path,name),module_path,apps)
    
    def _addModule(self, path, module_path, apps):
        if os.path.split(path)[1].startswith("."):
            return
        if path.endswith("~"):
            return

        #print(path)

        file = open(path)
        lines = file.readlines()
        file.close()

        if len(lines) == 0 or not lines[0].startswith("#%Module"):
            return

        env = application.ApplicationEnvironment()

        str = path[len(module_path)+1:]
        slash_pos = str.find("/")  # assumes Unix-style paths
        if slash_pos == -1:
            env.AppName = str
            env.AppVersion = None
        else:
            env.AppName = str[:slash_pos]
            env.AppVersion = str[slash_pos+1:]

        handle = application.ApplicationHandle()
        handle.Type = ApplicationHandle.MODULE
        if env.AppVersion is None:
            handle.Value = env.AppName
        else:
            handle.Value = env.AppName+"/"+env.AppVersion

        description = ""
        for line in lines:
            m = re.search("puts stderr \"([^\"]+)\"",line)
            if m is not None:
                if description != "":
                    description += " "
                description += m.group(1)
        if description != "":
            description = description.replace("$_module_name",handle.Value)
            if env.AppVersion is not None:
                description = description.replace("$version",env.AppVersion)
            description = description.replace("\\t"," ")
            description = description.replace("\\n","")
            description = re.sub(" +"," ",description)
            env.Description = description

        apps.add(env,[handle])

#######################################################################################################################
