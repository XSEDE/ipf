
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
import os
import sys
import time
import traceback

from ipf.error import WorkflowError
from ipf.paths import IPF_ETC_PATH, IPF_WORKFLOW_PATHS
from ipf.step import Step
from ipf.workflow import Workflow
from functools import reduce

#######################################################################################################################

logger = logging.getLogger(__name__)

#######################################################################################################################

class WorkflowEngine(object):
    def __init__(self):
        pass
        
    def run(self, workflow_file_name):
        workflow = Workflow()
        if os.path.isabs(workflow_file_name):
            workflow.read(workflow_file_name)
        else:
            for workflow_path in IPF_WORKFLOW_PATHS:
                workflow_path = os.path.join(workflow_path,workflow_file_name)
                if not os.path.isfile(workflow_path):
                    continue
                workflow.read(workflow_path)
            if workflow.name is None:
                raise WorkflowError("cannot open workflow file %s relative to any of IPF_WORKFLOW_PATHS" % \
                                    workflow_file_name)

        self._setDependencies(workflow)
        logger.debug(workflow)

        logger.info("starting workflow %s",workflow.name)
        for step in workflow.steps:
            try:
                step.start()
            except OSError as e:
                logger.error("failed to start step: %d (%s)\n" % (e.errno, e.strerror))
                logger.warn("aborting workflow")
                for step in workflow.steps:
                    if step.is_alive():
                        step.terminate()
                return

        start_time = time.time()
        steps_with_inputs = list(filter(self._sendNoMoreInputs,workflow.steps))
        while self._anyAlive(workflow.steps):
            if workflow.timeout is not None and time.time() - start_time > workflow.timeout:
                logger.warn("time out, terminating workflow")
                for step in workflow.steps:
                    if step.is_alive():
                        step.terminate()
                break
            time.sleep(0.1)
            steps_with_inputs = list(filter(self._sendNoMoreInputs,steps_with_inputs))

        for step in workflow.steps:
            step.join()

        if reduce(lambda b1,b2: b1 and b2, [step.exitcode == 0 for step in workflow.steps]):
            logger.info("workflow succeeded")
        else:
            logger.error("workflow failed")
            for step in workflow.steps:
                if step.exitcode == 0:
                    logger.info("  %10s succeeded (%s)",step.id,step.__class__.__name__)
                else:
                    logger.error(" %10s failed    (%s)",step.id,step.__class__.__name__)
                    
    def _anyAlive(self, steps):
        return reduce(lambda b1,b2: b1 or b2, [step.is_alive() for step in steps], False)

    def _sendNoMoreInputs(self, step):
        if self._anyAlive(step.depends_on):
            return True
        logger.debug("no more inputs to step %s",step.id)
        step.input_queue.put(None) # send None to indicate no more inputs
        step.input_queue.close()   # close the queue to stop the background thread
        return False
    
    def _setDependencies(self, workflow):
        for step in workflow.steps:
            step.depends_on = []  # [step, ...]
        for step in workflow.steps:
            for type in step.outputs:
                for dstep in step.outputs[type]:
                    dstep.depends_on.append(step)

#######################################################################################################################
