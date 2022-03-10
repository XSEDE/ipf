
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

import subprocess
import os
import sys
import re
import hashlib

from ipf.error import StepError
from . import application
from .types import AppEnvState, ApplicationHandle

#######################################################################################################################

valetPrefix = os.getenv('VALET_PREFIX')
if valetPrefix:
    valetLibPath = os.path.join(valetPrefix, 'lib', 'python')
    if valetLibPath not in sys.path:
        sys.path.append(valetLibPath)

import valet

class VALETApplicationsStep(application.ApplicationsStep):
    def __init__(self):
        application.ApplicationsStep.__init__(self)
        self._targetContext = valet.contexts.standard
        self._acceptParameter("default_support_contact",
                              "default to publish as SupportContact if no value is present in module file",
                              False)

    def _run(self):
        apps = application.Applications(self.resource_name, self.ipfinfo)
        self.support_contact = self.params.get("default_support_contact", False)
        #
        # Create a packageManager to facilitate finding and loading package definitions:
        #
        vmgr = valet.packageManager.sharedPackageManager()
        try:
            pkgIdList = vmgr.packageIdList(unify=True, context=self._targetContext)
            if pkgIdList is not None:
                #
                # Loop over all of the package ids that were provided:
                #
                for pkgId in pkgIdList:
                    #
                    # Load the package:
                    #
                    pkgs = vmgr.packagesWithId(pkgId, context=self._targetContext)
                    if pkgs is not None:
                        for pkg in pkgs:
                            #
                            # Get all versions of interest:
                            #
                            filteredVersions = sorted(pkg.filterVersions(byContext = self._targetContext), key = lambda v: v.id())
                            #
                            # Loop over all versions now:
                            #
                            for vers in filteredVersions:
                                versId = vers.id()

                                #
                                # Create the new application environment:
                                #
                                env = application.ApplicationEnvironment()
                                env.Extension["SupportStatus"] = "production"
                                if self.support_contact:
                                    env.Extension["SupportContact"] = self.support_contact

                                env.AppName = str(versId.packageId())
                                env.AppVersion = str(versId.versionAndFeatureString())
                                features = versId.features()
                                if len(features) > 0:
                                    env.Keywords = [x.stringValue() for x in features]

                                if vers.description() is not None:
                                    env.Description = vers.description()

                                # Take hash of path to uniquify the AppEnv and AppHandle IDs
                                path = pkg.sourceFile() + '|' + str(versId)
                                pathhashobject = hashlib.md5(path.encode('utf-8'))
                                env.path_hash = pathhashobject.hexdigest()

                                handle = application.ApplicationHandle()
                                handle.Type = ApplicationHandle.VALET
                                handle.Value = str(versId)

                                # env.ExecutionEnvironmentID = 'urn:ogf:glue2:xsede.org:ExecutionEnvironment:{:s}'.format(self.resource_name)
                                apps.add(env, [handle])

        except Exception as e:
            self.warning(str(e))
            return None

        return apps
