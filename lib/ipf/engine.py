#!/usr/bin/env python

import copy
import json
import logging
import logging.config
import os
import sys
import time
import traceback
import ConfigParser
import Queue

from ipf.document import Document
from ipf.error import IpfError, ReadDocumentError
from ipf.workflow import Workflow
from ipf.step import Step  # testing

#######################################################################################################################

ipfHome = os.environ.get("IPF_HOME")
if ipfHome == None:
    raise IpfError("IPF_HOME environment variable not set")
logging.config.fileConfig(os.path.join(ipfHome,"etc","logging.conf"))

logger = logging.getLogger(__name__)

#######################################################################################################################

def readConfig():
    ipfHome = os.environ.get("IPF_HOME")
    if ipfHome == None:
        raise IpfError("IPF_HOME environment variable not set")

    config = ConfigParser.ConfigParser()
    if os.path.exists(os.path.join(ipfHome,"etc","ipf.cfg")):
        config.read(os.path.join(ipfHome,"etc","ipf.cfg"))
    for file_name in os.listdir(os.path.join(ipfHome,"etc")):
        if file_name is not "ipf.cfg" and file_name.endswith(".cfg"):
            config.read(os.path.join(ipfHome,"etc",file_name))
    return config

#######################################################################################################################

class WorkflowEngine(object):
   
    def __init__(self):
        self.config = readConfig()
        
    def run(self, workflow_file_name):
        known_steps = self._readKnownSteps()

        workflow = Workflow()
        workflow.read(workflow_file_name,known_steps,self.config)

        self._setDependencies(workflow)
        logger.info(workflow)

        for step in workflow.steps:
            step.end_time = None
            step.start()

        no_more = set()
        while self._anyAlive(workflow.steps):
            #print("  still running")
            self._handleLogging(workflow.steps)
            self._handleOutputs(workflow.steps)
            self._sendNoMoreInputs(workflow.steps,no_more)
            time.sleep(1.0)  # reduce this after testing
        self._handleOutputs(workflow.steps)  # in case any are hanging around

        for step in workflow.steps:
            if step.exitcode == 0:
                logger.info("  %s succeeded" % step.id)
            else:
                logger.info("  %s failed" % step.id)

    def _anyAlive(self, steps):
        for step in steps:
            if step.is_alive():
                return True
        return False

    def _handleLogging(self, steps):
        for step in steps:
            try:
                while(True):
                    [source,step_id,level,message] = step.logging_queue.get(False)
                    logger = logging.getLogger(source)
                    if level == "ERROR":
                        logger.error("%s %s",step_id,message)
                    elif level == "WARNING":
                        logger.warning("%s %s",step_id,message)
                    elif level == "INFO":
                        logger.info("%s %s",step_id,message)
                    elif level == "DEBUG":
                        logger.debug("%s %s",step_id,message)
                    else:
                        logger.log(level,"%s %s",step_id,message)
                    #print("%s %s %s" % (level,id,message))
            except Queue.Empty:
                pass    # it's ok

    def _handleOutputs(self, steps):
        for step in steps:
            try:
                while(True):
                    document = step.output_queue.get(False)
                    logger.info("output of document %s from %s" % (document.type,step.id))
                    #logger.debug(document)
                    if document.type in step.outputs:
                        logger.info("  routing to %d steps" % len(step.outputs[document.type]))
                        for dest_step in step.outputs[document.type]:
                            logger.debug("    routing to %s" % dest_step.id)
                            dest_step.input_queue.put(document)
            except Queue.Empty:
                pass    # it's ok

    def _sendNoMoreInputs(self, steps, no_more):
        cur_time = time.time()
        for step in steps:
            if step.id in no_more:
                continue
            if not step.is_alive():
                continue
            if self._anyAlive(step.depends_on):
                continue
            # potential timing issue - could be outputs in transit
            #   below is a bit of a hack to address this
            if step.end_time is None:
                step.end_time = cur_time
            if cur_time - step.end_time > 5:
                logger.info("no more inputs to step %s" % step.id)
                step.input_queue.put(Step.NO_MORE_INPUTS)
                no_more.add(step.id)
    
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
        #modules = self._readModules("/share/home/00415/wsmith/glue2/lib/steps/teragrid", "steps.teragrid")

        for module in modules:
            logger.debug("loading %s",module)
            try:
                __import__(module)
            except ImportError:
                traceback.print_exc()

        classes = []
        stack = Step.__subclasses__()
        while len(stack) > 0:
            cls = stack.pop(0)
            classes.append(cls)
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
        
    def _readKnownStepsOld(self):
        ipfHome = os.environ.get("IPF_HOME")
        if ipfHome == None:
            raise IpfError("IPF_HOME environment variable not set")

        steps = []
        file = open(os.path.join(ipfHome,"var","known_steps.json"))
        doc = json.load(file)
        file.close()
        for step_doc in doc:
            step = ProgramStep()
            step.fromJson(step_doc)
            if step.name is not None:
                steps.append(step)
        return steps

#######################################################################################################################
