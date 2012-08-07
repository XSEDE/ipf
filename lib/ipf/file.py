
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

import os
import sys
import time

from ipf.error import StepError
from ipf.home import IPF_HOME
from ipf.step import PublishStep

#######################################################################################################################

class FilePublishStep(PublishStep):
    def __init__(self):
        PublishStep.__init__(self)

        self.description = "publishes documents by writing them to a file"
        self.time_out = 5
        self._acceptParameter("path",
                              "Path to the file to write. If the path is relative, it is relative to $IPF_HOME/var/.",
                              True)


    def run(self):
        file = open(self._getPath(),"w")
        while True:
            data = self.input_queue.get(True)
            if data == None:
                break
            for rep_class in self.publish:
                if rep_class.data_cls != data.__class__:
                    continue
                rep = rep_class(data)
                self.info("writing data %s with id %s using representation %s",data.__class__,data.id,rep_class)
                file.write(rep.get())
                file.flush()
                break
        file.close()

    def _getPath(self):
        try:
            path = self.params["path"]
        except KeyError:
            raise StepError("path parameter not specified")
        if os.path.isabs(path):
            return path
        return os.path.join(IPF_HOME,"var",path)
        
#######################################################################################################################
