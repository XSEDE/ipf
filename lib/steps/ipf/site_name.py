#!/bin/env python

###############################################################################
#   Copyright 2011 The University of Texas at Austin                          #
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

from ipf.document import Document
from ipf.error import StepError
from ipf.step import Step

#######################################################################################################################

class SiteNameStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "ipf/site_name"
        self.description = "produces a site name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.produces_types = ["ipf/site_name.txt",
                               "ipf/site_name.json",
                               "ipf/site_name.xml"]
        self.accepts_params["site_name"] = "a hard coded site name (optional)"

    def run(self):
        try:
            site_name = self.params["site_name"]
        except KeyError:
            host_name = socket.getfqdn()
            # assumes that the site name is all except first component
            try:
                index = host_name.index(".") + 1
            except ValueError:
                self.error("host name does not appear to be fully qualified")
                raise StepError("host name does not appear to be fully qualified")
            site_name = host_name[index:]

        self._output(SiteNameDocumentTxt(site_name))
        self._output(SiteNameDocumentJson(site_name))
        self._output(SiteNameDocumentXml(site_name))

#######################################################################################################################

class SiteNameDocumentTxt(Document):
    def __init__(self, site_name):
        Document.__init__(self, site_name, "ipf/site_name.txt")
        self.site_name = site_name
        self.body = "%s\n" % site_name

class SiteNameDocumentJson(Document):
    def __init__(self, site_name):
        Document.__init__(self, site_name, "ipf/site_name.json")
        self.site_name = site_name
        self.body = "{\"siteName\": \"%s\"}\n" % site_name

class SiteNameDocumentXml(Document):
    def __init__(self, site_name):
        Document.__init__(self, site_name, "ipf/site_name.xml")
        self.site_name = site_name
        self.body = "<SiteName>%s</SiteName>\n" % site_name
