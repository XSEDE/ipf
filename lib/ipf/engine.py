#!/usr/bin/env python

import copy
import json
import logging
import logging.config
import os
import sys
import time
import traceback

from ipf.document import Document
from ipf.error import IpfError, ReadDocumentError
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
        known_steps = self._readKnownSteps()

        workflow = Workflow()
        workflow.read(workflow_file_name,known_steps)

        self._setDependencies(workflow)
        logger.info(workflow)

        for step in workflow.steps:
            step.start()

        steps_with_inputs = filter(self._sendNoMoreInputs,workflow.steps)
        while self._anyAlive(workflow.steps):
            time.sleep(1.0)  # reduce this after testing
            steps_with_inputs = filter(self._sendNoMoreInputs,steps_with_inputs)

        if reduce(lambda b1,b2: b1 and b2, map(lambda step: step.exitcode == 0, workflow.steps)):
            logger.info("workflow succeeded")
        else:
            logger.error("workflow failed")
            for step in workflow.steps:
                if step.exitcode == 0:
                    logger.info("  %10s succeeded (%s)",step.id,step.name)
                else:
                    logger.error("  %10s failed    (%s)",step.id,step.name)
                    
    def _anyAlive(self, steps):
        for step in steps:
            if step.is_alive():
                return True
        return False

    def _sendNoMoreInputs(self, step):
        if self._anyAlive(step.depends_on):
            return True
        logger.debug("no more inputs to step %s",step.id)
        step.input_queue.put(Step.NO_MORE_INPUTS)
        return False
    
    def _setDependencies(self, workflow):
        for step in workflow.steps:
            step.depends_on = []  # [step, ...]
        for step in workflow.steps:
            for type in step.outputs:
                for dstep in step.outputs[type]:
                    dstep.depends_on.append(step)

    def _readKnownSteps(self):
        ipf_home = os.environ.get("IPF_HOME")
        if ipf_home == None:
            raise IpfError("IPF_HOME environment variable not set")
        path = os.path.join(ipf_home,"lib","steps")
        mod_path = "steps"
        modules = self._readModules(path, mod_path)

        for module in modules:
            logger.debug("loading %s",module)
            try:
                __import__(module)
            except ImportError:
                traceback.print_exc()

        classes = {}
        stack = Step.__subclasses__()
        while len(stack) > 0:
            cls = stack.pop(0)
            step = cls({})
            if step.name in classes:
                logger.warn("multiple step classes with name %s - ignoring all but first",step.name)
            else:
                classes[step.name] = cls
            stack.extend(cls.__subclasses__())

        return classes

    def _readModules(self, path, mod_path):
        modules = []
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path,file)):
                mods = self._readModules(os.path.join(path,file),mod_path+"."+file)
                modules.extend(mods)
            elif os.path.isfile(os.path.join(path,file)):
                if file.endswith(".py") and file != "__init__.py":
                    mod,ext = os.path.splitext(file)
                    modules.append(mod_path+"."+mod)
        return modules

#######################################################################################################################
