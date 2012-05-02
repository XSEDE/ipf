#!/usr/bin/env python

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

import os
import time
import ConfigParser

from ipf.engine import StepEngine
from ipf.error import StepError
from ipf.step import Step

#######################################################################################################################

class FilePublishStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "ipf/publish/file"
        self.description = "publishes documents by writing them to a file"
        self.time_out = 5
        self.requires_types = []
        self.produces_types = []
        self.accepts_params["path"] = "Path to the file to write. If the path is relative, it is relative to $IPF_HOME/var/."

        self.file = None
        self.more_inputs = True

    def run(self):
        while self.more_inputs:
            time.sleep(1)

    def input(self, document):
        if self.file is None:
            self.file = open(self._getPath(),"w")
        self.file.write(document.body)

    def _getPath(self):
        if "path" not in self.params:
            raise StepError("path parameter not specified")
        path = self.params["path"]
        if os.path.isabs(path):
            return path
        ipfHome = os.environ.get("IPF_HOME")
        if ipfHome == None:
            raise StepError("IPF_HOME environment variable not set")
        return os.path.join(ipfHome,"var",path)

    def noMoreInputs(self):
        if self.more_inputs:
            self.more_inputs = False
            if self.file is not None:
                self.file.close()

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(FilePublishStep())
