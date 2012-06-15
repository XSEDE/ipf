#!/usr/bin/env python

import copy
import json
import logging
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

logger = logging.getLogger(__name__)

class Workflow(object):
    def __init__(self):
        self.name = None
        self.steps = []

    def __str__(self):
        wstr = "Workflow %s\n" % self.name
        for step in self.steps:
            wstr += step.__str__("  ")
        return wstr

    def read(self, file_name, known_steps, config):

        file = open(file_name,"r")
        try:
            doc = json.load(file)
        except ValueError, e:
            raise WorkflowError("could not parse workflow file %s: %s" % (file_name,e))
        file.close()

        if not "steps" in doc:
            raise WorkflowError("no steps specified")

        self.name = doc.get("name","workflow")
        for step_doc in doc["steps"]:
            params = step_doc.get("params",{})
            #params["id"] = step_doc.get("id")
            #params["requires_types"] = step_doc.get("requires_types",[])

            if "name" not in step_doc:
                raise WorkflowError("workflow step does not specify the 'name' of the step to run")
            try:
                # if any info in the config applies to the step, add it to params ?
                step = known_steps[step_doc["name"]](params)
            except KeyError:
                raise WorkflowError("no step is known with name '%s'" % step_doc["name"])

            self.steps.append(step)

        self._inferDetails(known_steps)

    def _inferDetails(self, known_steps):
        known_types = {}
        for kstep in known_steps.values():
            for type in kstep({}).produces_types:
                if type not in known_types:
                    known_types[type] = []
                known_types[type].append(kstep)

        self._addMissingSteps(known_types)
        self._connectSteps()

    def _addMissingSteps(self, known_types):
        ptypes = {}
        rtypes = {}
        for step in self.steps:
            for ptype in step.produces_types:
                if ptype not in ptypes:
                    ptypes[ptype] = []
                ptypes[ptype].append(step)
            for rtype in step.requires_types:
                if rtype not in rtypes:
                    rtypes[rtype] = []
                rtypes[rtype].append(step)

        added_step = True
        while added_step:
            added_step = False
            for rtype in rtypes:
                if rtype in ptypes:
                    continue
                if rtype not in known_types:
                    raise WorkflowError("no known step that produces type '%s'" % rtype)
                if len(known_types[rtype]) > 1:
                    raise WorkflowError("more than one step produces type '%s' - can't infer which to use" % rtype)
                new_step = known_types[rtype][0]({})
                self.steps.append(new_step)
                logger.info("adding step %s" % new_step.name)
                for ptype in new_step.produces_types:
                    if ptype not in ptypes:
                        ptypes[ptype] = []
                    ptypes[ptype].append(new_step)
                for rtype in new_step.requires_types:
                    if not rtype in rtypes:
                        rtypes[rtype] = []
                    rtypes[rtype].append(new_step)
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

        step_map = {}
        for step in self.steps:
            step_map[step.id] = step

        for step in self.steps:
            step.outputs = {}
            if step.output_ids is not None:
                for type in step.output_ids:
                    step.outputs[type] = []
                    for id in step.output_ids[type]:
                        try:
                            step.outputs[type].append(step_map[id])
                        except KeyError:
                            raise WorkflowError("step %s wants to send output to unknown step %s" % (step.id,id))
            else:
                for ptype in step.produces_types:
                    if ptype in rtypes:
                        step.outputs[ptype] = rtypes[ptype]
            step.requested_types = []
            for type in step.outputs:
                step.requested_types.append(type)

    def _checkConnections(self):
        pass

#######################################################################################################################
