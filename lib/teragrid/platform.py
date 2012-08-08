
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

import commands
import time
import sys

from ipf.data import Data, Representation
from ipf.step import Step
from ipf.name import ResourceName

#######################################################################################################################

class PlatformStep(Step):

    def __init__(self):
        Step.__init__(self)

        self.description = "produces a platform name using tgwhatami"
        self.time_out = 5
        self.requires = [ResourceName]
        self.produces = [TeraGridPlatform]
        self._acceptParameter("tgwhatami","path to the tgwhatami program (default 'tgwhatami')",False)
        self._acceptParameter("platform","hard coded name of the TeraGrid platform (optional)",False)

    def run(self):
        rn_doc = self._getInput("ipf/resource_name.txt")

        try:
            platform = self.params["platform"]
        except KeyError:
            try:
                tg_whatami = self.params["tgwhatami"]
            except KeyError:
                tg_whatami = "tgwhatami"
            (status, output) = commands.getstatusoutput(tg_whatami)
            if status != 0:
                self.error("failed to execute %s" % tg_whatami)
                sys.exit(1)
            platform = output

        self._output(PlatformDocumentTxt(rn_doc.body,platform))
        self._output(PlatformDocumentJson(rn_doc.body,platform))
        self._output(PlatformDocumentXml(rn_doc.body,platform))

#######################################################################################################################

class TeraGridPlatform(Data):
    def __init__(self, resource_name, platform):
        Document.__init__(self, resource_name, "teragrid/platform.txt")
        self.platform = platform

#######################################################################################################################

class TeraGridPlatformTxt(Representation):
    data_cls = TeraGridPlatform

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.platform

class TeraGridPlatformJson(Representation):
    data_cls = TeraGridPlatform

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return "{platform: \"%s\"}\n" % self.data.platform
        return self.data.platform


class TeraGridPlatformXml(Representation):
    data_cls = TeraGridPlatform

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return "<Platform>%s</Platform>\n" % self.data.platform

#######################################################################################################################
