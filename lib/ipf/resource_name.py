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

from ipf.data import Data, Representation
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
