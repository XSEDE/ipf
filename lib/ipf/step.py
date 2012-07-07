
###############################################################################
#   Copyright 2011 The University of Texas at Austin                          #
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
import json
import logging
import multiprocessing
import os
import threading
import urlparse

from ipf.document import Document
from ipf.error import NoMoreInputsError
from ipf.error import StepError

#######################################################################################################################

class Step(multiprocessing.Process):
    NO_MORE_INPUTS = "NO_MORE_INPUTS"

    def __init__(self, params):
        multiprocessing.Process.__init__(self)

        self.name = ""
        self.description = None
        self.time_out = None
        self.requires_types = []
        self.produces_types = []
        self.accepts_params = {"id": "an identifier for this step",
                               "requested_types": "comma-separated list of the types this step should produce"}

        try:
            self.id = params["id"]
            del params["id"]
        except KeyError:
            self.id = None
        # delete?
        try:
            self.requested_types = params["requested_types"]
            del params["requested_types"]
        except KeyError:
            self.requested_types = self.produces_types
        # to hard code links between steps
        try:
            self.output_ids = params["outputs"]
            del params["outputs"]
        except KeyError:
            self.output_ids = None

        # should test that params is valid against accepts_params
        self.params = params
        
        self.input_queue = multiprocessing.Queue()
        self.inputs = []  # input documents received from input_queue, but not yet wanted
        self.no_more_inputs = False

        self.logger = logging.getLogger(self._logName())

    def __str__(self, indent=""):
        sstr = indent+"Step %s\n" % self.id
        sstr += indent+"  name:  %s\n" % self.name
        sstr += indent+"  description: %s\n" % self.description
        if self.time_out is None:
            sstr += indent+"  time out: None\n"
        else:
            sstr += indent+"  time out: %d secs\n" % self.time_out
        sstr += indent+"  parameters:\n"
        for param in self.params:
            sstr += indent+"    %s: %s\n" % (param,self.params[param])
        sstr += indent+"  requires types:\n"
        for type in self.requires_types:
            sstr += indent+"    %s\n" % type
        sstr += indent+"  produces types:\n"
        for type in self.produces_types:
            sstr += indent+"    %s\n" % type
        sstr += indent+"  requested types:\n"
        for type in self.requested_types:
            sstr += indent+"    %s\n" % type

        # set/used by workflow
        sstr += indent+"  outputs:\n"
        try:
            for type in self.outputs:
                for step in self.outputs[type]:
                    sstr += indent+"    %s -> %s\n" % (type,step.id)
        except AttributeError:
            pass
        return sstr

    def _getInput(self, type):
        for index in range(0,len(self.inputs)):
            if self.inputs[index].type == type:
                return self.inputs.pop(index)
        if self.no_more_inputs:
            waiting = []
            for input in self.inputs:
                waiting.append(input.type)
            raise NoMoreInputsError("No more inputs and no waiting message of type %s. Waiting messages: %s" %
                                    (type,waiting))
        while True:
            doc = self.input_queue.get(True)
            if doc == Step.NO_MORE_INPUTS:
                self.no_more_inputs = True
                raise NoMoreInputsError("no more inputs while waiting for %s" % type)
            if doc.type == type:
                return doc
            else:
                self.inputs.append(doc)

    def run(self):
        """Run the step - the Engine will have this in its own thread."""
        raise StepError("Step.run not overridden")

    def _output(self, document):
        if document.type not in self.outputs:
            return
        self.info("output %s",document.type)
        for step in self.outputs[document.type]:
            self.debug("sending output %s to step %s",document.type,step.id)
            step.input_queue.put(document)

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
