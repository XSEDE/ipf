#!/bin/env python

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

import socket
import sys

from ipf.data import Data, Representation
from ipf.error import StepError
from ipf.step import Step

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
