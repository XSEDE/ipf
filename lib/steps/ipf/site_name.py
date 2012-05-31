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

import copy
import socket
import sys

from ipf.document import Document
from ipf.step import Step

#######################################################################################################################

class SiteNameStep(Step):
    name = "ipf/hostname"
    description = "produces a site name document using the fully qualified domain name of the host"
    time_out = 5
    produces_types = ["ipf/site_name.txt",
                      "ipf/site_name.json",
                      "ipf/site_name.xml"]
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["sitename"] = "a hard coded site name (optional)"
    accepts_params["hostname"] = "a hard coded host name (optional)"

    def __init__(self, params):
        Step.__init__(self,params)

    def run(self):
        try:
            site_name = self.params["sitename"]
        except KeyError:
            try:
                host_name = self.params["hostname"]
            except KeyError:
                host_name = socket.getfqdn()
            # assumes that the site name is all except first component
            try:
                index = host_name.index(".") + 1
            except ValueError:
                self.error("host name does not appear to be fully qualified")
                sys.exit(1)

            site_name = host_name[index:]

        if "ipf/site_name.txt" in self.requested_types:
            self.output_queue.put(SiteNameDocumentTxt(site_name))
        if "ipf/site_name.json" in self.requested_types:
            self.output_queue.put(SiteNameDocumentJson(site_name))
        if "ipf/site_name.xml" in self.requested_types:
            self.output_queue.put(SiteNameDocumentXml(site_name))

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
