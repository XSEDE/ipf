
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
import threading
import time
import Queue

from ipf.catalog import catalog
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

    def read(self, file_name):
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
            if "name" not in step_doc:
                raise WorkflowError("workflow step does not specify the 'name' of the step to run")
            try:
                step = catalog.steps[step_doc["name"]]()
                step.setParameters(dict(doc.get("params",{}).items()+step_doc.get("params",{}).items()))
            except KeyError:
                raise WorkflowError("no step is known with name '%s'" % step_doc["name"])

            self.steps.append(step)

        self._inferDetails()

    def _inferDetails(self):
        self._addMissingSteps()
        self._connectSteps()

    def _addMissingSteps(self):
        required = set()
        for step in self.steps:
            for cls in step.requires:
                required.add(cls)
            
        for step in self.steps:
            self._removeProduced(step,required)

        while len(required) > 0:
            cls = required.pop()
            producers = catalog.producers.get(cls,[])
            if len(producers) == 0:
                raise WorkflowError("no known step that produces %s" % cls)
            if len(producers) > 1:
                raise WorkflowError("more than one step produces %s - can't infer which to use" % cls)
            step = producers[0]()
            step.setParameters({})
            self.steps.append(step)
            self._removeProduced(step,required)

    def _removeProduced(self, step, required):
        for data in step.produces:
            try:
                required.remove(data)
            except KeyError:
                pass
            try:
                reps = catalog.reps_for_data.get(data,[])
                for rep in reps:
                    try:
                        required.remove(rep)
                    except KeyError:
                        pass
            except KeyError:
                pass

    def _connectSteps(self):
        for i in range(0,len(self.steps)):
            if self.steps[i].id is None:
                self.steps[i].id = "step-%d" % (i+1)
        ids = set()
        for step in self.steps:
            if step.id in ids:
                raise WorkflowError("at least two steps have an id of '%s'" % step.id)
            ids.add(step.id)

        outputs = {}
        for step in self.steps:
            for data in step.requires:
                if not data in outputs:
                    outputs[data] = []
                outputs[data].append(step)

        for step in self.steps:
            step.outputs = {}
            for data in step.produces:
                if data in outputs:
                    step.outputs[data] = outputs[data]

    def _checkConnections(self):
        pass

#######################################################################################################################
