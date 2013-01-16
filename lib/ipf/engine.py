
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

import copy
import json
import logging
import logging.config
import os
import sys
import time
import traceback

from ipf.home import IPF_HOME
from ipf.step import Step
from ipf.workflow import Workflow

#######################################################################################################################

logging.config.fileConfig(os.path.join(IPF_HOME,"etc","logging.conf"))
logger = logging.getLogger(__name__)

#######################################################################################################################

class WorkflowEngine(object):
    def __init__(self):
        pass
        
    def run(self, workflow_file_name):
        workflow = Workflow()
        if not os.path.isabs(workflow_file_name):
            workflow_file_name = os.path.join(IPF_HOME,"etc","workflow",workflow_file_name)
        workflow.read(workflow_file_name)

        self._setDependencies(workflow)
        logger.debug(workflow)

        logger.info("starting workflow %s",workflow.name)
        for step in workflow.steps:
            step.start()

        start_time = time.time()
        steps_with_inputs = filter(self._sendNoMoreInputs,workflow.steps)
        while self._anyAlive(workflow.steps):
            if workflow.timeout is not None and time.time() - start_time > workflow.timeout:
                logger.warn("time out, terminating workflow")
                for step in workflow.steps:
                    if step.is_alive():
                        step.terminate()
                break
            time.sleep(0.1)
            steps_with_inputs = filter(self._sendNoMoreInputs,steps_with_inputs)

        # wait again, in case we terminated
        while self._anyAlive(workflow.steps):
            time.sleep(0.1)

        if reduce(lambda b1,b2: b1 and b2, map(lambda step: step.exitcode == 0, workflow.steps)):
            logger.info("workflow succeeded")
        else:
            logger.error("workflow failed")
            for step in workflow.steps:
                if step.exitcode == 0:
                    logger.info("  %10s succeeded (%s)",step.id,step.__class__.__name__)
                else:
                    logger.error(" %10s failed    (%s)",step.id,step.__class__.__name__)
                    
    def _anyAlive(self, steps):
        return reduce(lambda b1,b2: b1 or b2, map(lambda step: step.is_alive(), steps), False)

    def _sendNoMoreInputs(self, step):
        if self._anyAlive(step.depends_on):
            return True
        logger.debug("no more inputs to step %s",step.id)
        step.input_queue.put(None)
        return False
    
    def _setDependencies(self, workflow):
        for step in workflow.steps:
            step.depends_on = []  # [step, ...]
        for step in workflow.steps:
            for type in step.outputs:
                for dstep in step.outputs[type]:
                    dstep.depends_on.append(step)

#######################################################################################################################
