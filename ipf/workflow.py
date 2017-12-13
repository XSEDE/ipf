
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
from forkablepdb import ForkablePdb

from ipf.catalog import catalog
from ipf.error import *
    
#######################################################################################################################

logger = logging.getLogger(__name__)

class Workflow(object):
    def __init__(self):
        self.name = None
        self.steps = []
        self.timeout = None    # the number of seconds to wait for the workflow to complete

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

        ForkablePdb().set_trace()
        if "timeout" in doc:
            self.timeout = doc["timeout"]

        if not "steps" in doc:
            raise WorkflowError("no steps specified")

        self.name = doc.get("name","workflow")
        for step_doc in doc["steps"]:
            if "name" not in step_doc:
                raise WorkflowError("workflow step does not specify the 'name' of the step to run")
            try:
                step = catalog.steps[step_doc["name"]]()
            except KeyError:
                raise WorkflowError("no step is known with name '%s'" % step_doc["name"])
            step.configure(step_doc,doc.get("params",{}))

            self.steps.append(step)

        self._inferDetails()

    def _inferDetails(self):
        self._addMissingSteps()
        self._connectSteps()

    def _addMissingSteps(self):
        requires = set()
        ForkablePdb().set_trace()
        for step in self.steps:
            self._addRequires(step,requires)
        produces = set()
        for step in self.steps:
            self._addProduces(step,produces)

        missing = requires - produces
        while len(missing) > 0:
            cls = missing.pop()
            producers = catalog.producers.get(cls,[])
            if len(producers) == 0:
                raise WorkflowError("no known step that produces %s" % cls)
            if len(producers) > 1:
                raise WorkflowError("more than one step produces %s - can't infer which to use" % cls)
            step = producers[0]()
            step.configure({"params":{}},{})
            self.steps.append(step)
            self._addRequires(step,requires)
            self._addProduces(step,produces)
            # added steps could in turn require more steps to be added
            missing = requires - produces

    def _addRequires(self, step, requires):
        for cls in step.requires:
            requires.add(cls)
            
    def _addProduces(self, step, produces):
        for data in step.produces:
            produces.add(data)
            reps = catalog.reps_for_data.get(data,[])
            for rep in reps:
                produces.add(rep)

    def _connectSteps(self):
        steps = {}
        for i in range(0,len(self.steps)):
            if self.steps[i].id is None:
                self.steps[i].id = "step-%d" % (i+1)
            steps[self.steps[i].id] = self.steps[i]
        ids = set()
        for step in self.steps:
            if step.id in ids:
                raise WorkflowError("at least two steps have an id of '%s'" % step.id)
            ids.add(step.id)

        for step in self.steps:
            step.remaining_requires = set(step.requires)

        for step in self.steps:
            if len(step.output_ids) > 0:
                for cls in step.output_ids:
                    step.outputs[cls] = []
                    for id in step.output_ids[cls]:
                        try:
                            step.outputs[cls].append(steps[id])
                        except KeyError:
                            raise WorkflowError("step %s specifies unknown step '%s' as output" % (step.id,id))
                        steps[id].remaining_requires.remove(cls)

        # just for checking validity of workflow
        produces = set()
        for step in self.steps:
            for data in step.produces:
                if data in step.outputs:
                    continue
                if data in produces:
                    raise WorkflowError("multiple steps produce %s.%s without specifying output steps" % \
                                        (data.__module__,data.__name__))
                produces.add(step)

        requires = {}
        for step in self.steps:
            for data in step.remaining_requires:
                if not data in requires:
                    requires[data] = []
                requires[data].append(step)

        for step in self.steps:
            for data in step.produces:
                if data in step.outputs:
                    continue
                if data in requires:
                    step.outputs[data] = requires[data]

    def _checkConnections(self):
        pass

#######################################################################################################################
