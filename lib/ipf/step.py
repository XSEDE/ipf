
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
#import logging
import os
import sys
import threading
import urlparse

import ConfigParser

from ipf.document import Document
from ipf.error import *

#logger = logging.getLogger()
#handler = logging.FileHandler(os.path.join(ipfHome,"var","step.log"))
#formatter = logging.Formatter("%(asctime)s %(levelname)s - %(name)s %(message)s")
#handler.setFormatter(formatter)
#logger.addHandler(handler)
#logger.setLevel(logging.WARN)

#######################################################################################################################

class Step(object):
    def __init__(self):
        self.name = None
        self.description = None
        self.time_out = None
        self.requires_types = []
        self.produces_types = []
        self.accepts_params = {"id": "an identifier for this step",
                               "requested_types": "comma-separated list of the types this step should produce"}
        self.params = {}

        self.engine = None
        self.id = None
        self.requested_types = []

    def setup(self, engine, params):
        self.engine = engine
        self.id = None
        self.requested_types = []

        if "id" in params:
            self.id = params["id"]
            del params["id"]
        else:
            self.id = self.name
        if "requested_types" in params:
            self.requested_types = params["requested_types"].split(",")
            del params["requested_types"]
        else:
            self.requested_types = self.produces_types

        self.params = params

    def run(self):
        """Run the step - the Engine will have this in its own thread."""
        raise StepError("Step.run not overridden")

    def input(self, document):
        raise StepError("Step.input not overridden")

    def noMoreInputs(self):
        raise StepError("Step.noMoreInputs not overridden")

    def error(self, message):
        self.engine.stepError(self,message)

    def warning(self, message):
        self.engine.stepWarning(self,message)

    def info(self, message):
        self.engine.stepInfo(self,message)

    def debug(self, message):
        self.engine.stepDebug(self,message)

#######################################################################################################################
