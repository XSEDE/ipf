
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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
import logging
import multiprocessing
import time
from Queue import Empty

from ipf.data import Data,Representation
from ipf.home import IPF_HOME
from ipf.error import NoMoreInputsError, StepError

#######################################################################################################################

class Step(multiprocessing.Process):

    def __init__(self):
        multiprocessing.Process.__init__(self)

        self.id = None        # a unique id for the step in a workflow
        self.description = None
        self.time_out = None
        self.params = {}
        self.requires = []    # Data or Representation that this step requires
        self.produces = []    # Data that this step produces

        self.accepts_params = {}
        self._acceptParameter("id","an identifier for this step",False)
        self._acceptParameter("requires","list of additional types this step requires",False)
        self._acceptParameter("outputs","list of ids for steps that output should be sent to (typically not needed)",
                              False)
        
        self.input_queue = multiprocessing.Queue()
        self.inputs = []  # input data received from input_queue, but not yet wanted
        self.no_more_inputs = False

        self.outputs = {}  # steps to send outputs to. keys are data.name, values are lists of steps

        self.logger = logging.getLogger(self._logName())

    def setParameters(self, workflow_params, step_params):
        self._checkUnexpectedParameters(step_params)
        self.params = dict(workflow_params.items()+step_params.items())
        self._checkExpectedParameters(self.params)

        self.id = self.params.get("id",None)

        from ipf.catalog import catalog    # can't import this at the top - circular import
        for name in self.params.get("requires",[]):
            try:
                cls = catalog.data[name]
            except KeyError:
                raise StepError("%s is not a known data" % name)
            self.requires.append(cls)

        try:
            self.output_ids = self.params["outputs"]
        except KeyError:
            self.output_ids = []

    def _acceptParameter(self, name, description, required):
        self.accepts_params[name] = (description,required)

    def _checkUnexpectedParameters(self, params):
        for name in params:
            if not self._acceptsParameter(name):
                self.info("received an unexpected parameter: %s - %s",name,params[name])

    def _checkExpectedParameters(self, params):
        for name in self.accepts_params:
            if self._requiresParameter(name):
                if name not in params:
                    raise StepError("required parameter %s not provided" % name)

    def _acceptsParameter(self, name):
        if name in self.accepts_params:
            return True
        return False

    def _requiresParameter(self, name):
        if name not in self.accepts_params:
            return False
        return self.accepts_params[name][1]

    def __str__(self, indent=""):
        if self.id is None:
            sstr = indent+"Step:\n"
        else:
            sstr = indent+"Step %s:\n" % self.id
        sstr += indent+"  name: %s.%s\n" % (self.__module__,self.__class__.__name__)
        sstr += indent+"  description: %s\n" % self.description
        if self.time_out is None:
            sstr += indent+"  time out: None\n"
        else:
            sstr += indent+"  time out: %d secs\n" % self.time_out
        if len(self.params) > 0:
            sstr += indent+"  parameters:\n"
            for param in self.params:
                sstr += indent+"    %s: %s\n" % (param,self.params[param])
        sstr += indent+"  requires:\n"
        for cls in self.requires:
            sstr += indent+"    %s.%s\n" % (cls.__module__,cls.__name__)
        sstr += indent+"  produces:\n"
        for cls in self.produces:
            sstr += indent+"    %s.%s\n" % (cls.__module__,cls.__name__)
        if len(self.outputs) > 0:
            sstr += indent+"  outputs:\n"
            for cls in self.outputs:
                for step in self.outputs[cls]:
                    sstr += indent+"    %s.%s -> %s\n" % (cls.__module__,cls.__name__,step.id)

        return sstr

    def _getInput(self, cls):
        # need to handle Representations, too
        for index in range(0,len(self.inputs)):
            if self.inputs[index].__class__ == cls:
                return self.inputs.pop(index)
        if self.no_more_inputs:
            raise NoMoreInputsError("No more inputs and none of the %d waiting message is a %s." %
                                    (len(self.inputs),cls))
        while True:
            data = self.input_queue.get(True)
            if data == None:
                self.no_more_inputs = True
                raise NoMoreInputsError("no more inputs while waiting for %s" % cls)
            if data.__class__ == cls:
                return data
            else:
                self.inputs.append(data)

    def run(self):
        """Run the step - the Engine will have this in its own thread."""
        raise StepError("Step.run not overridden")

    def _output(self, data):
        if data.__class__ not in self.outputs:
            return
        self.debug("output %s",data)
        for step in self.outputs[data.__class__]:
            self.debug("sending output %s to step %s",data,step.id)
            # isolate any changes to the data by queuing copies
            step.input_queue.put(copy.deepcopy(data))

    def _logName(self):
        return self.__module__ + "." + self.__class__.__name__

    def error(self, msg, *args, **kwargs):
        args2 = (self.id,)+args
        self.logger.error("%s - "+msg,*args2,**kwargs)

    def warning(self, msg, *args, **kwargs):
        args2 = (self.id,)+args
        self.logger.warning("%s - "+msg,*args2,**kwargs)

    def info(self, msg, *args, **kwargs):
        args2 = (self.id,)+args
        self.logger.info("%s - "+msg,*args2,**kwargs)

    def debug(self, msg, *args, **kwargs):
        args2 = (self.id,)+args
        self.logger.debug("%s - "+msg,*args2,**kwargs)

#######################################################################################################################

class PublishStep(Step):

    def __init__(self):
        Step.__init__(self)

        self.accepts_params = {}
        self._acceptParameter("publish","a list of representations to publish",True)

        self.publish = []

    def setParameters(self, workflow_params, step_params):
        Step.setParameters(self,workflow_params,step_params)
        try:
            publish_names = self.params["publish"]
        except KeyError:
            raise StepError("required parameter 'publish' not specified")

        from ipf.catalog import catalog    # can't import this at the top - circular import
        for name in publish_names:
            try:
                rep_class = catalog.representations[name]
                self.publish.append(rep_class)
            except KeyError:
                raise StepError("unknown representation %s" % name)
            if not rep_class.data_cls in self.requires:
                self.requires.append(rep_class.data_cls)

    def run(self):
        while True:
            data = self.input_queue.get(True)
            if data == None:
                break
            for rep_class in self.publish:
                if rep_class.data_cls != data.__class__:
                    continue
                rep = rep_class(data)
                self._publish(rep)
                break

#######################################################################################################################

class TriggerStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.accepts_params = {}
        self._acceptParameter("trigger","a list of representations to trigger on",False)
        self._acceptParameter("minimum_interval","the minimum interval in seconds between triggers",False)
        self._acceptParameter("maximum_interval","the maximum interval in seconds between triggers",False)

        self.trigger = []
        self.minimum_interval = None
        self.maximum_interval = None

        self.last_trigger = None
        self.next_trigger = None

    def setParameters(self, workflow_params, step_params):
        Step.setParameters(self,workflow_params,step_params)
        trigger_names = self.params.get("trigger",[])

        from ipf.catalog import catalog    # can't import this at the top - circular import
        for name in trigger_names:
            try:
                rep_class = catalog.representations[name]
                self.trigger.append(rep_class)
            except KeyError:
                raise StepError("unknown representation %s" % name)
            if not rep_class.data_cls in self.requires:
                self.requires.append(rep_class.data_cls)

    def run(self):
        try:
            self.minimum_interval = self.params["minimum_interval"]
            self.last_trigger = time.time()
        except KeyError:
            pass
        try:
            self.maximum_interval = self.params["maximum_interval"]
            self.next_trigger = time.time() + self.maximum_interval
        except KeyError:
            pass

        if len(self.trigger) and self.maximum_interval is None:
            raise StepError("You must specify at least one trigger or a maximum_interval")

        if len(self.trigger) == 0:
            self._runPeriodic()
        else:
            self._runTrigger()

    def _runPeriodic(self):
        while True:
            self._doTrigger(None)
            time.sleep(self.maximum_interval)

    def _runTrigger(self):
        while True:
            try:
                data = self.input_queue.get(True,1)
            except Empty:
                if self.next_trigger is not None and time.time() >= self.next_trigger:
                    # if it has been too long since the last trigger, send one
                    self._doTrigger(None)
            else:
                if data == None:
                    # no more data will be sent, the step can end
                    break
                for rep_class in self.trigger:
                    if rep_class.data_cls != data.__class__:
                        continue
                    rep = rep_class(data)
                    if self.last_trigger is None or time.time() - self.last_trigger > self.minimum_interval:
                        # trigger if it isn't too soon since the last one
                        self._doTrigger(rep)
                    else:
                        # pull forward the next trigger if it is too soon
                        self.next_trigger = self.last_trigger + self.minimum_interval
                    break

    def _doTrigger(self, representation):
        if self.minimum_interval is not None:
            self.last_trigger = time.time()
        if self.maximum_interval is not None:
            self.next_trigger = time.time() + self.maximum_interval
        else:
            self.next_trigger = None
        self._trigger(representation)

#######################################################################################################################

class WorkflowStep(TriggerStep):
    def __init__(self):
        TriggerStep.__init__(self)
        self.description = "runs a workflow on triggers under constraints"
        self._acceptParameter("workflow","the workflow description file to execute",True)

    def _trigger(self, representation):
        try:
            workflow_file = self.params["workflow"]
        except KeyError:
            raise StepError("required parameter 'workflow' not specified")

        self.info("running workflow %s",workflow_file)
        # error if import is above
        from ipf.engine import WorkflowEngine
        engine = WorkflowEngine()
        engine.run(workflow_file)

##############################################################################################################
