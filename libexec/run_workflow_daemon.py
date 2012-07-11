
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

import os
import sys

from ipf.daemon import Daemon
from ipf.home import IPF_HOME

min_version = (2,6)
max_version = (2,9)

if sys.version_info < min_version or sys.version_info > max_version:
    print(stderr,"Python version 2.6 or 2.7 is required")
    sys.exit(1)

from ipf.engine import WorkflowEngine

#######################################################################################################################

class WorkflowDaemon(Daemon):
    def __init__(self, workflow_path):
        self.workflow_path = workflow_path

        (path,workflow_filename) = os.path.split(workflow_path)
        name = workflow_filename.split(".")[0]

        Daemon.__init__(self,
                        pidfile=os.path.join(IPF_HOME,"var",name+".pid"),
                        stdout=os.path.join(IPF_HOME,"var",name+".log"),
                        stderr=os.path.join(IPF_HOME,"var",name+".log"))

    def run(self):
        engine = WorkflowEngine()
        engine.run(self.workflow_path)

#######################################################################################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: run_workflow_daemon.py <workflow file>")
        sys.exit(1)

    daemon = WorkflowDaemon(sys.argv[1])
    daemon.start()
