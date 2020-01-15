
###############################################################################
#   Copyright 2014 The University of Texas at Austin                          #
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

import logging
import logging.config
import optparse
import os
import sys

min_version = (3,6)
max_version = (3,9)

if sys.version_info < min_version or sys.version_info > max_version:
    print(sys.stderr,"Python version 3.6 or newer is required")
    sys.exit(1)

from ipf.daemon import OneProcessWithRedirect,Daemon
from ipf.engine import WorkflowEngine
from ipf.paths import *

#######################################################################################################################

logging.config.fileConfig(os.path.join(IPF_ETC_PATH,"logging.conf"))

#######################################################################################################################

class WorkflowDaemon(Daemon):
    def __init__(self, workflow_path):
        self.workflow_path = workflow_path

        (path,workflow_filename) = os.path.split(workflow_path)
        name = workflow_filename.split(".")[0]

        Daemon.__init__(self,
                        pidfile=os.path.join(IPF_VAR_PATH,name+".pid"),
                        stdout=os.path.join(IPF_LOG_PATH,name+".log"),
                        stderr=os.path.join(IPF_LOG_PATH,name+".log"))

    def run(self):
        engine = WorkflowEngine()
        engine.run(self.workflow_path)

#######################################################################################################################

class OneWorkflowOnly(OneProcessWithRedirect):
    def __init__(self, workflow_path):
        self.workflow_path = workflow_path
        (path,workflow_filename) = os.path.split(workflow_path)
        name = workflow_filename.split(".")[0]

        OneProcessWithRedirect.__init__(self,
                                        pidfile=os.path.join(IPF_VAR_PATH,name+".pid"),
                                        stdout=os.path.join(IPF_LOG_PATH,name+".log"),
                                        stderr=os.path.join(IPF_LOG_PATH,name+".log"))

    def run(self):
        engine = WorkflowEngine()
        engine.run(self.workflow_path)

#######################################################################################################################

def main():
    usage = "Usage: %prog [options] <workflow file>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-d","--daemon",action="store_true",default=False,dest="daemon",
                      help="run as a daemon")
    parser.add_option("-c","--cron",action="store_true",default=False,dest="cron",
                      help="running out of cron")
    (options, args) = parser.parse_args()
    if options.daemon and options.cron:
        parser.error("can't run as both daemon and cron")
    if len(args) != 1:
        parser.error("exactly one positional argument expected - a path to a workflow file")

    if options.daemon:
        daemon = WorkflowDaemon(args[0])
        daemon.start()
    elif options.cron:
        # don't let processes pile up if workflows aren't finishing
        workflow = OneWorkflowOnly(args[0])
        workflow.start()
    else:
        engine = WorkflowEngine()
        engine.run(args[0])

#######################################################################################################################

if __name__ == "__main__":
    main()
