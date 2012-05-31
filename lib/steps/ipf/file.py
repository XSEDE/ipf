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

import copy
import os
import sys
import time

from ipf.step import Step

#######################################################################################################################

class FilePublishStep(Step):
    name = "ipf/publish/file"
    description = "publishes documents by writing them to a file"
    time_out = 5
    accepts_params = copy.copy(Step.accepts_params)
    accepts_params["requires_types"] = "The type of documents that will be published"
    accepts_params["path"] = "Path to the file to write. If the path is relative, it is relative to $IPF_HOME/var/."

    def __init__(self, params):
        Step.__init__(self,params)

        if "requires_types" in params:
            self.requires_types = copy.copy(FilePublishStep.requires_types)
            self.requires_types.extend(params["requires_types"])

    def run(self):
        more_inputs = True
        file = open(self._getPath(),"w")
        while more_inputs:
            doc = self.input_queue.get(True)
            if doc == Step.NO_MORE_INPUTS:
                more_inputs = False
            else:
                self.info("writing document of type %s" % doc.type)
                file.write(doc.body)
        file.close()

    def _getPath(self):
        if "path" not in self.params:
            self.error("path parameter not specified")
            sys.exit(1)
        path = self.params["path"]
        if os.path.isabs(path):
            return path
        ipfHome = os.environ.get("IPF_HOME")
        if ipfHome == None:
            self.error("IPF_HOME environment variable not set")
            sys.exit(1)
        return os.path.join(ipfHome,"var",path)

#######################################################################################################################
