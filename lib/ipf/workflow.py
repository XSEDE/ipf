#!/usr/bin/env python

import copy
import json
import os
import subprocess
import sys
import threading
import time
import ConfigParser
import Queue

from ipf.document import Document
from ipf.error import *
from ipf.step import Step

#######################################################################################################################

class ProgramStep(Step):
    def __init__(self):
        Step.__init__(self)
        self.executable = None
        self.modification_time = None
        self.name = None
        self.description = None
        self.time_out = None
        self.requires_types = []
        self.produces_types = []
        self.accepts_params = {}

    def __eq__(self, other):
        if other == None:
            return False
        return self.executable == other.executable

    def __str__(self):
        sstr = "Step\n"
        sstr += "  name:  %s\n" % self.name
        sstr += "  description: %s\n" % self.description
        sstr += "  executable: %s\n" % self.executable
        sstr += "  time out: %d secs\n" % self.time_out
        sstr += "  requires types:\n"
        for type in self.requires_types:
            sstr += "    %s\n" % type
        sstr += "  produces types:\n"
        for type in self.produces_types:
            sstr += "    %s\n" % type
        sstr += "  accepts parameters:\n"
        for param in self.accepts_params:
            sstr += "    %s: %s\n" % (param,self.accepts_params[param])
        return sstr

    def toJson(self):
        doc = {}
        if self.executable is None:
            raise StepError("executable not specified")
        doc["executable"] = self.executable
        if self.modification_time is None:
            raise StepError("modification time not specified")
        doc["modification_time"] = self.modification_time
        if self.name is not None:
            doc["name"] = self.name
        if self.description is not None:
            doc["description"] = self.description
        if self.time_out is not None:
            doc["time_out"] = self.time_out
        doc["requires_types"] = self.requires_types
        doc["produces_types"] = self.produces_types
        doc["accepts_params"] = self.accepts_params
        return doc

    def fromJson(self, doc):
        try:
            self.executable = doc["executable"]
            self.modification_time = doc["modification_time"]
        except KeyError, e:
            print("didn't find required information for the step: %s" % e)
            raise e
        self.name = doc.get("name")
        self.description = doc.get("description")
        self.time_out = doc.get("time_out")
        self.requires_types = doc.get("requires_types",[])
        self.produces_types = doc.get("produces_types",[])
        self.accepts_params = doc.get("accepts_params",{})
    
    def discover(self, executable):
        self.executable = executable
        
        proc = subprocess.Popen([executable,"-i"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        proc.wait()

        if stderr != "":
            print(stderr)

        if proc.returncode != 0:
            raise StepError("    failed (error code %d)" % (proc.returncode))
            #raise StepError("    failed (error code %d):\n%s" % (proc.returncode,stderr))

        try:
            doc = json.loads(stdout)
        except ValueError, e:
            print("failed to parse step information: %s" % e)
            print(stdout)
            raise e

        #print(json.dumps(doc,sort_keys=True,indent=4))
        try:
            self.name = doc["name"]
            self.description = doc["description"]
            self.time_out = doc["time_out"]
            self.requires_types = doc["requires_types"]
            self.produces_types = doc["produces_types"]
            self.accepts_params = doc["accepts_params"]
        except KeyError, e:
            print("didn't find required information for the step: %s" % e)
            raise e
        #print("    discovered %s" % self)

#######################################################################################################################

class WorkflowStep(ProgramStep, threading.Thread):
    def __init__(self, prog_step):
        threading.Thread.__init__(self)
        ProgramStep.__init__(self)

        self.executable = prog_step.executable
        self.name = prog_step.name
        self.description = prog_step.description
        self.time_out = prog_step.time_out
        self.requires_types = copy.copy(prog_step.requires_types)
        self.produces_types = copy.copy(prog_step.produces_types)
        self.accepts_params = copy.copy(prog_step.accepts_params)

        self.id = None
        self.params = {}
        self.inputs = Queue.Queue()    # input documents
        self.no_more_inputs_time = None
        self.outputs = {}    # document type -> [step, ...]    used when running the workflow
        self.proc = None

    def __str__(self, indent=""):
        sstr = indent+"Step %s\n" % self.id
        sstr += indent+"  name:  %s\n" % self.name
        sstr += indent+"  description: %s\n" % self.description
        sstr += indent+"  executable: %s\n" % self.executable
        sstr += indent+"  time out: %d secs\n" % self.time_out
        sstr += indent+"  parameters:\n"
        for param in self.params:
            sstr += indent+"    %s: %s\n" % (param,self.params[param])
        sstr += indent+"  requires types:\n"
        for type in self.requires_types:
            sstr += indent+"    %s\n" % type
        sstr += indent+"  outputs types:\n"
        for type in self.outputs:
            for step in self.outputs[type]:
                sstr += indent+"    %s -> %s\n" % (type,step.id)
        return sstr

    def run(self):
        if len(self.outputs) > 0:
            requested_types = None
            for type in self.outputs:
                if requested_types is None:
                    requested_types = type
                else:
                    requested_types += "," + type
            self.params["requested_types"] = requested_types

        command = self.executable
        for name in self.params:
            command += " %s=%s" % (name,self.params[name])

        self.debug("running %s" % command)
        self.proc = subprocess.Popen(command,shell=True,
                                     stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        thread = threading.Thread(target=self._readOutputs)
        thread.start()

        while self.proc.poll() is None:
            try:
                document = self.inputs.get(True,0.25)
                self.debug("writing document to stdin of process")
                document.write(self.proc.stdin)
            except Queue.Empty:
                pass
            if self.no_more_inputs_time != None:
                self.info("closing stdin")
                self.proc.stdin.close()
                break
        self.info("waiting for process to complete")
        while self.proc.poll() is None:
            cur_time = time.time()
            if cur_time - self.no_more_inputs_time > self.time_out:
                self.proc.kill()
                self.error("failed to complete in %d seconds" % self.time_out)
            time.sleep(0.25)

        self.debug("waiting for output thread to complete...")
        thread.join()
        err_msgs = self.proc.stderr.read()
        if err_msgs != "":
            self.error(err_msgs)
        self.info("done")

    def _readOutputs(self):
        try:
            while True:
                doc = Document.read(self.proc.stdout)
                #self.debug("read output document:\n %s" % doc.body)
                self.engine.output(self,doc)
        except ReadDocumentError:
            self.info("no more outputs for step %s" % self.id)
            pass

    def input(self, document):
        self.debug("input received")
        self.inputs.put(document)

    def noMoreInputs(self):
        if self.no_more_inputs_time is None:
            self.no_more_inputs_time = time.time()

#######################################################################################################################

class Workflow(object):
    def __init__(self):
        self.name = None
        self.steps = []

    def __str__(self):
        wstr = "Workflow %s\n" % self.name
        for step in self.steps:
            wstr += step.__str__("  ")
        return wstr

    def read(self, file_name, known_steps):

        file = open(file_name,"r")
        try:
            doc = json.load(file)
        except ValueError, e:
            raise WorkflowError("could not parse workflow file %s: %s" % (file_name,e))
        file.close()

        if not "steps" in doc:
            raise WorkflowError("no steps specified")

        self.name = doc.get("name","")
        for step_doc in doc["steps"]:
            step = None
            if "name" not in step_doc:
                raise WorkflowError("workflow step does not specify the 'name' of the step to run")
            for kstep in known_steps:
                if kstep.name == step_doc["name"]:
                    step = WorkflowStep(kstep)
                    break
            if step == None:
                raise WorkflowError("no step is known with name '%s'" % step_doc["name"])

            step.id = step_doc.get("id")
            #step.inputs = step_doc.get("inputs",[])
            for type in step_doc.get("requires_types",[]):
                step.requires_types.append(type)
            step.params = step_doc.get("params",{})

            self.steps.append(step)

        self._inferDetails(known_steps)

    def _inferDetails(self, known_steps):
        known_types = {}
        for kstep in known_steps:
            for type in kstep.produces_types:
                if type not in known_types:
                    known_types[type] = []
                known_types[type].append(kstep)

        for ktype in known_types:
            kstr = "%45s:" % ktype
            for step in known_types[ktype]:
                kstr += " "+step.name
            print(kstr)

        self._addMissingSteps(known_types)
        self._connectSteps()

    def _addMissingSteps(self, known_types):
        ptypes = set()
        rtypes = set()
        for step in self.steps:
            for ptype in step.produces_types:
                if ptype in ptypes:
                    raise WorkflowError("type %s produced by two or more steps in the workflow")
                ptypes.add(ptype)
            for rtype in step.requires_types:
                rtypes.add(rtype)

        added_step = True
        while added_step:
            added_step = False
            for rtype in rtypes:
                if rtype in ptypes:
                    continue
                if rtype not in known_types:
                    raise WorkflowError("no step is known that produces type '%s'" % rtype)
                if len(known_types[rtype]) > 1:
                    raise WorkflowError("more than one step produces type '%s' - can't infer which to use" % rtype)
                new_step = WorkflowStep(known_types[rtype][0])
                self.steps.append(new_step)
                print("adding step %s" % new_step.name)
                for ptype in new_step.produces_types:
                    if ptype in ptypes:
                        raise WorkflowError("type %s produced by two or more steps in the workflow")
                    ptypes.add(ptype)
                for rtype in new_step.requires_types:
                    rtypes.add(rtype)
                added_step = True
                break

    def _connectSteps(self):
        for i in range(0,len(self.steps)):
            if self.steps[i].id is None:
                self.steps[i].id = "step-%d" % (i+1)
        ids = set()
        for step in self.steps:
            if step.id in ids:
                raise WorkflowError("at least two steps have an id of '%s'" % step.id)
            ids.add(step.id)
            
        rtypes = {}
        for step in self.steps:
            for rtype in step.requires_types:
                if rtype not in rtypes:
                    rtypes[rtype] = []
                rtypes[rtype].append(step)
        for step in self.steps:
            step.outputs = {}
            for ptype in step.produces_types:
                if ptype in rtypes:
                    step.outputs[ptype] = rtypes[ptype]

#######################################################################################################################
