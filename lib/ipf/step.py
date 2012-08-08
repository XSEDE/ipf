
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

import commands
import copy
import json
import logging
import multiprocessing
import os
import threading
import urlparse

from ipf.data import Data,Representation
from ipf.home import IPF_HOME
from ipf.error import NoMoreInputsError, StepError

#######################################################################################################################

class Step(multiprocessing.Process):

    def __init__(self):
        multiprocessing.Process.__init__(self)

        self.description = None
        self.time_out = None
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

    def setParameters(self, params):
        self.id = params.get("id",None)

        self._checkParameters(params)
        self.params = params

        from ipf.catalog import catalog    # can't import this at the top - circular import
        for name in params.get("requires",[]):
            try:
                cls = catalog.data[name]
            except KeyError:
                raise StepError("%s is not a known data" % name)
            self.requires.append(cls)

        try:
            self.output_ids = params["outputs"]
        except KeyError:
            self.output_ids = []

    def _acceptParameter(self, name, description, required):
        self.accepts_params[name] = (description,required)

    def _checkParameters(self, params):
        for name in params:
            if not self._acceptsParameter(name):
                self.info("received an unexpected parameter: %s - %s",name,params[name])
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
            sstr += indent+"    %s\n" % cls
        sstr += indent+"  produces:\n"
        for cls in self.produces:
            sstr += indent+"    %s\n" % cls
        if len(self.outputs) > 0:
            sstr += indent+"  outputs:\n"
            for cls in self.outputs:
                for step in self.outputs[cls]:
                    sstr += indent+"    %s -> %s\n" % (cls,step.id)

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

    def setParameters(self, params):
        Step.setParameters(self,params)
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

#######################################################################################################################
