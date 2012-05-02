#!/usr/bin/env python

import copy
import json
import optparse
import os
import select
import subprocess
import stat
import sys
import threading
import time
import ConfigParser

from ipf.document import Document
from ipf.error import IpfError, ReadDocumentError
from ipf.workflow import ProgramStep, Workflow

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

class Engine(object):
    def __init__(self):
        # don't use config files - have config info in workflow definitions?
        self.config = readConfig()

    def output(self, step, document):
        pass

    def error(self, message):
        pass

    def warn(self, message):
        pass

    def info(self, message):
        pass

    def debug(self, message):
        pass

    def stepError(self, step, message):
        self.error("%s - %s" % (step.id,message))

    def stepWarning(self, step, message):
        self.warn("%s - %s" % (step.id,message))

    def stepInfo(self, step, message):
        self.info("%s - %s" % (step.id,message))

    def stepDebug(self, step, message):
        self.debug("%s - %s" % (step.id,message))

#######################################################################################################################

class StepEngine(Engine):
    """This class is used to run a Step as a stand alone process."""
    
    def __init__(self, step):
        Engine.__init__(self)
        self.step = step
        self.handle()
        
    def handle(self):
        parser = optparse.OptionParser(usage="usage: %prog [options] <param=value>*")
        parser.set_defaults(info=False)
        parser.add_option("-i","--info",action="store_true",dest="info",
                          help="output information about this step in JSON")
        (options,args) = parser.parse_args()

        if options.info:
            info = {}
            info["name"] = self.step.name
            info["description"] = self.step.description
            info["time_out"] = self.step.time_out
            info["requires_types"] = self.step.requires_types
            info["produces_types"] = self.step.produces_types
            info["accepts_params"] = self.step.accepts_params
            print(json.dumps(info,sort_keys=True,indent=4))
            sys.exit(0)

        # someone wants to run the step and all arguments are name=value properties

        params = {}
        for arg in args:
            (name,value) = arg.split("=")
            params[name] = value
            
        self.step.setup(self,params)

        self.step_thread = threading.Thread(target=self._runStep)
        self.step_thread.start()
        self.run()

    def _runStep(self):
        try:
            self.step.run()
        except Exception, e:
            self.stepError(self.step,str(e))

    def run(self):
        wait_time = 0.2
        while not sys.stdin.closed and self.step_thread.isAlive():
            try:
                rfds, wfds, efds = select.select([sys.stdin], [], [], wait_time)
            except KeyboardInterrupt:
                sys.stdin.close()
                self.step.noMoreInputs()
            if len(rfds) == 0:
                continue
            
            try:
                document = Document.read(sys.stdin)
                self.step.input(document)
            except ReadDocumentError:
                sys.stdin.close()
                self.step.noMoreInputs()
        self.step_thread.join()

    def output(self, step, document):
        document.source = step.id
        document.write(sys.stdout)

    def error(self, message):
        sys.stderr.write("ERROR: %s\n" % message)

    def warn(self, message):
        sys.stderr.write("WARN: %s\n" % message)

    def info(self, message):
        sys.stderr.write("INFO: %s\n" % message)

    def debug(self, message):
        sys.stderr.write("DEBUG: %s\n" % message)

#######################################################################################################################

class WorkflowEngine(Engine):
    def __init__(self):
        Engine.__init__(self)

    def error(self, message):
        # use a logger instead
        sys.stderr.write("ERROR: %s\n" % message)

    def warn(self, message):
        sys.stderr.write("WARN: %s\n" % message)

    def info(self, message):
        sys.stderr.write("INFO: %s\n" % message)

    def debug(self, message):
        sys.stderr.write("DEBUG: %s\n" % message)

    def output(self, step, document):
        self.info("output of document %s from %s" % (document.type,step.id))
        if document.type in step.outputs:
            self.info("  routing to %d steps" % len(step.outputs[document.type]))
            for dest_step in step.outputs[document.type]:
                dest_step.input(document)
        
    def run(self, workflow_file_name):
        known_steps = self._readKnownSteps()

        workflow = Workflow()
        workflow.read(workflow_file_name,known_steps)
        for step in workflow.steps:
            step.engine = self

        self.info(workflow)

        self._setDependencies(workflow)

        for step in workflow.steps:
            step.start()

        no_more = set()
        while self._anyAlive(workflow.steps):
            for step in workflow.steps:
                if not step.isAlive():
                    continue
                if self._anyAlive(step.depends_on):
                    continue
                if not step.id in no_more:
                    self.info("no more inputs for step %s" % step.id)
                    step.noMoreInputs()
                    no_more.add(step.id)
            print("  still running")
            time.sleep(1.0)  # reduce this after testing

    def _anyAlive(self, steps):
        for step in steps:
            if step.isAlive():
                return True
        return False
    
    def _setDependencies(self, workflow):
        for step in workflow.steps:
            step.depends_on = []  # [step, ...]
        for step in workflow.steps:
            for type in step.outputs:
                for dstep in step.outputs[type]:
                    dstep.depends_on.append(step)

        for step in workflow.steps:
            dstr = "%s depends on:" % step.id
            for dstep in step.depends_on:
                dstr += " %s" % dstep.id
            print(dstr)

    def _readKnownSteps(self):
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
