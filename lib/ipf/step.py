
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
import optparse
import os
import select
import sys
import threading
import urlparse

import ConfigParser

from ipf.document import Document
from ipf.engine import Engine
from ipf.error import *

#logger = logging.getLogger()
#handler = logging.FileHandler(os.path.join(ipfHome,"var","step.log"))
#formatter = logging.Formatter("%(asctime)s %(levelname)s - %(name)s %(message)s")
#handler.setFormatter(formatter)
#logger.addHandler(handler)
#logger.setLevel(logging.WARN)

#######################################################################################################################

class Step:
    def __init__(self, params={}):
        self.name = None
        self.description = None
        self.time_out = None
        self.requires_types = []
        self.produces_types = []
        self.params=params

        # these are set by the engine
        self.engine = None
        self.id = None
        self.requested_types = []

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

class StepEngine(Engine):
    """This class is used to run a Step as a stand alone process."""
    
    def __init__(self, step):
        Engine.__init__(self)
        step.engine = self
        self.step = step
        self.handle()
        
    def handle(self):
        parser = optparse.OptionParser(usage="usage: %prog [options] <param=value>*\n"+ \
                                       "         two common parameters are:\n" + \
                                       "           ipf.step.id=<id>\n" + \
                                       "           ipf.step.requested_types=<requested_type><,requested_type>*\n")
        parser.set_defaults(info=False)
        parser.add_option("-i","--info",action="store_true",dest="info",
                          help="output information about this step in JSON")
        (options,args) = parser.parse_args()

        if options.info:
            info = {}
            info["name"] = self.step.name
            info["description"] = self.step.description
            info["timeout"] = self.step.time_out
            info["requires_types"] = self.step.requires_types
            info["produces_types"] = self.step.produces_types
            print(json.dumps(info,sort_keys=True,indent=4))
            sys.exit(0)

        # someone wants to run the step and all arguments are name=value properties

        props = {}
        for arg in args:
            (name,value) = arg.split("=")
            props[name] = value
            
        if "ipf.step.id" in props:
            self.step.id = props["ipf.step.id"]
            del props["ipf.step.id"]
        else:
            self.step.id = self.step.name
        if "ipf.step.requested_types" in props:
            self.step.requested_types = props["ipf.step.requested_types"].split(",")
            del props["ipf.step.requested_types"]
        else:
            self.step.requested_types = self.step.produces_types

        #self.step_thread = threading.Thread(target=self.step.run)
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
            rfds, wfds, efds = select.select([sys.stdin], [], [], wait_time)
            if len(rfds) == 0:
                continue
            try:
                document = Document.read(sys.stdin)
                self.step.input(document)
            except ReadDocumentError:
                # log an error under some conditions?
                pass
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

    def stepError(self, step, message):
        self.error("%s - %s" % (step.id,message))

    def stepWarning(self, step, message):
        self.warn("%s - %s" % (step.id,message))

    def stepInfo(self, step, message):
        self.info("%s - %s" % (step.id,message))

    def stepDebug(self, step, message):
        self.debug("%s - %s" % (step.id,message))

#######################################################################################################################
