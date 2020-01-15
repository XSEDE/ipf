
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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
import socket
import sys

import ipf.sysinfo
from ipf.error import StepError

#######################################################################################################################

class ResourceNameStep(ipf.sysinfo.ResourceNameStep):
    def __init__(self):
        ipf.sysinfo.ResourceNameStep.__init__(self)
        self.description = "produces a resource name document using tgwhereami"
        self._acceptParameter("tgwheremi","path to the tgwhereami program (default 'tgwhereami')",False)

    def run(self):
        try:
            resource_name = self.params["resource_name"]
        except KeyError:
            tg_whereami = self.params.get("tgwhereami","tgwhereami")
            (status, output) = subprocess.getstatusoutput(tg_whereami)
            if status != 0:
                raise StepError("failed to execute %s: %s" % (tg_whereami,output))
            resource_name = output

        self._output(ipf.sysinfo.ResourceName(resource_name))
    
#######################################################################################################################

class SiteNameStep(ipf.sysinfo.SiteNameStep):

    def __init__(self):
        ipf.sysinfo.SiteNameStep.__init__(self)

        self.description = "produces a site name document using tgwhereami"
        self._acceptParameter("tgwhereami","path to the tgwhereami program (default 'tgwhereami')",False)

    def run(self):
        try:
            site_name = self.params["site_name"]
        except KeyError:
            tg_whereami = self.params.get("tgwhereami","tgwhereami")
            (status, output) = subprocess.getstatusoutput(tg_whereami+" -s")
            if status != 0:
                raise StepError("failed to execute %s: %s" % (tg_whereami,output))
            site_name = output

        self._output(ipf.sysinfo.SiteName(site_name))

#######################################################################################################################

class PlatformStep(ipf.sysinfo.PlatformStep):

    def __init__(self):
        ipf.sysinfo.PlatformStep.__init__(self)
        self._acceptParameter("tgwhatami","path to the tgwhatami program (default 'tgwhatami')",False)

    def run(self):
        try:
            tg_whatami = self.params["tgwhatami"]
        except KeyError:
            tg_whatami = "tgwhatami"
        (status, output) = subprocess.getstatusoutput(tg_whatami)
        if status != 0:
            raise StepError("failed to execute %s" % tg_whatami)
        return output

#######################################################################################################################
