
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
import logging
import os
import sys

from ipf.data import Data, Representation
from ipf.step import Step
from ipf.sysinfo import ResourceName

##############################################################################################################

class UserPortalLoadStep(Step):

    def __init__(self):
        Step.__init__(self)

        self.description = "produces a document describing the load on a resource by running the TeraGrid user portal providers"
        self.time_out = 15
        self.requires = [ResourceName]
        self.produces = [UserPortalLoad]
        self._acceptParameter("provider_script",
                              "the path to the provider script (default 'tg_user_portal_provider')",
                              False)
        self._acceptParameter("source",
                              "the source of the load information (typically a scheduler or resource name)",
                              True)

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name

        try:
            script = self.params["provider_script"]
        except KeyError:
            script = "tg_user_portal_provider"
        try:
            source = self.params["source"]
        except KeyError:
            raise StepError("source not specified")

        cmd = "%s %s %s %s load" % (script,self.resource_name,source,source)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError(cmd+" failed: "+output+"\n")
        self._output(UserPortalLoad(self.resource_name,output))

#######################################################################################################################

class UserPortalLoad(Data):
    def __init__(self, id, xml):
        Data.__init__(self,id)
        self.xml = xml

#######################################################################################################################

class UserPortalLoadXml(Representation):
    data_cls = UserPortalLoad

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.data.xml

#######################################################################################################################

class UserPortalJobsStep(Step):

    def __init__(self):
        Step.__init__(self)

        self.description = "produces a document describing the jobs on a resource by running the TeraGrid user portal providers"
        self.time_out = 15
        self.requires = [ResourceName]
        self.produces = [UserPortalJobs]
        self._acceptParameter("provider_script",
                              "the path to the provider script (default 'tg_user_portal_provider')",
                              False)
        self._acceptParameter("source",
                              "the source of the jobs information (typically a scheduler or resource name)",
                              True)

        self.resource_name = None

    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name

        try:
            script = self.params["provider_script"]
        except KeyError:
            script = "tg_user_portal_provider"
        try:
            source = self.params["source"]
        except KeyError:
            raise StepError("source not specified")

        cmd = "%s %s %s %s jobs" % (script,self.resource_name,source,source)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError(cmd+" failed: "+output+"\n")
        self._output(UserPortalJobs(self.resource_name,output))

#######################################################################################################################

class UserPortalJobs(Data):
    def __init__(self, id, xml):
        Data.__init__(self,id)
        self.xml = xml

#######################################################################################################################

class UserPortalJobsXml(Representation):
    data_cls = UserPortalJobs

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.data.xml

#######################################################################################################################
