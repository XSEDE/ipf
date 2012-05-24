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
import ConfigParser

from ipf.documents.site_name import *
from ipf.engine import StepEngine
import ipf.step

#######################################################################################################################

class HostNameStep(ipf.step.Step):
    def __init__(self, params={}):
        ipf.step.Step.__init__(self,params)

        self.name = "ipf/hostname"
        self.description = "produces a site name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.requires_types = []
        self.produces_types = ["ipf/site_name.txt",
                               "ipf/site_name.json",
                               "ipf/site_name.xml"]

    def run(self):
        try:
            host_name = self.engine.config.get("default","hostname")
        except ConfigParser.NoSectionError:
            host_name = socket.getfqdn()

        # assumes that the site name is all except first component
        try:
            index = host_name.index(".") + 1
        except ValueError:
            raise StepError("host name does not appear to be fully qualified")

        site_name = host_name[index:]

        if "ipf/site_name.txt" in self.requested_types:
            self.engine.output(self,SiteNameDocumentTxt(site_name))
        if "ipf/site_name.json" in self.requested_types:
            self.engine.output(self,SiteNameDocumentJson(site_name))
        if "ipf/site_name.xml" in self.requested_types:
            self.engine.output(self,SiteNameDocumentXml(site_name))

#######################################################################################################################

if __name__ == "__main__":
    ipf.step.StepEngine(HostNameStep())
