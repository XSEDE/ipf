
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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

import platform
import socket

from ipf.data import Data, Representation
from ipf.error import StepError
from ipf.step import Step

#######################################################################################################################

class ResourceNameStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces a resource name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.produces = [ResourceName]
        self._acceptParameter("resource_name","a hard coded host name",False)

    def run(self):
        try:
            resource_name = self.params["resource_name"]
        except KeyError:
            resource_name = socket.getfqdn()

        self._output(ResourceName(resource_name))

#######################################################################################################################

class ResourceName(Data):
    def __init__(self, resource_name):
        Data.__init__(self,resource_name)
        self.resource_name = resource_name

#######################################################################################################################

class ResourceNameTxt(Representation):
    data_cls = ResourceName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.resource_name

class ResourceNameJson(Representation):
    data_cls = ResourceName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return "{\"resourceName\": \"%s\"}\n" % self.data.resource_name

class ResourceNameXml(Representation):
    data_cls = ResourceName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return "<ResourceName>%s</ResourceName>\n" % self.data.resource_name

#######################################################################################################################

class SiteNameStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces a site name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.produces = [SiteName]
        self._acceptParameter("site_name","a hard coded site name",False)
        
    def run(self):
        try:
            site_name = self.params["site_name"]
        except KeyError:
            host_name = socket.getfqdn()
            # assumes that the site name is all except first component
            try:
                index = host_name.index(".") + 1
            except ValueError:
                raise StepError("host name does not appear to be fully qualified")
            site_name = host_name[index:]

        self._output(SiteName(site_name))

#######################################################################################################################

class SiteName(Data):
    def __init__(self, site_name):
        Data.__init__(self,site_name)
        self.site_name = site_name

#######################################################################################################################

class SiteNameTxt(Representation):
    data_cls = SiteName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.site_name

class SiteNameJson(Representation):
    data_cls = SiteName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_Application_JSON,data)

    def get(self):
        return "{\"siteName\": \"%s\"}\n" % self.data.site_name

class SiteNameXml(Representation):
    data_cls = SiteName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return "<SiteName>%s</SiteName>\n" % self.data.site_name

#######################################################################################################################

class PlatformStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "Produces a platform string."
        self.time_out = 10
        self.requires = [ResourceName]
        self.produces = [Platform]
        self._acceptParameter("platform","A hard-coded platform string",False)

    def run(self):
        resource_name = self._getInput(ResourceName).resource_name
        try:
            plat = self.params["platform"]
        except KeyError:
            self._output(Platform(resource_name,self._run()))
        else:
            self._output(Platform(resource_name,plat))

    def _run(self):
        os_name = platform.system().lower()
        (name,version,id) = platform.linux_distribution()
        distribution = name.lower() + version[0]
        arch = platform.processor()
        return "%s-%s-%s" % (os_name,distribution,arch)

#######################################################################################################################

class Platform(Data):
    def __init__(self, id, plat):
        Data.__init__(self,id)
        self.platform = plat

    def __str__(self):
        return "%s" % self.platform

#######################################################################################################################

class PlatformTxt(Representation):
    data_cls = Platform

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.platform

#######################################################################################################################

class SystemInformationStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces a document with basic information about a host"
        self.time_out = 5
        self.requires = [ResourceName,SiteName,Platform]
        self.produces = [SystemInformation]

    def run(self):
        self._output(SystemInformation(self._getInput(ResourceName).resource_name,
                                       self._getInput(SiteName).site_name,
                                       self._getInput(Platform).platform))


#######################################################################################################################

class SystemInformation(Data):
    def __init__(self, resource_name, site_name, platform):
        Data.__init__(self,resource_name)
        self.resource_name = resource_name
        self.site_name = site_name
        self.platform = platform

#######################################################################################################################

class SystemInformationTxt(Representation):
    data_cls = SystemInformation

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return "system %s at site %s is a %s\n" % (self.data.resource_name,self.data.site_name,self.data.platform)

#######################################################################################################################
