#!/usr/bin/env python

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

import os
import time
import ConfigParser

from ipf.engine import StepEngine
from ipf.step import Step

#######################################################################################################################

class AmqpPublishStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "ipf/publish/amqp"
        self.description = "publishes documents by via AMQP"
        self.time_out = 5
        self.requires_types = []
        self.produces_types = []
        self.accepts_params["service"] = "a list of alternative hosts (or host:ports) to try to connect to"
        self.accepts_params["vhost"] = "the AMQP virtual host to connect to"
        self.accepts_params["exchange"] = "the AMQP exchange to publish to"
        # credentials for ssl

        self.service = []
        self.vhost = None
        self.exchange = None

        self.connection = None
        self.channel = None

        self.more_inputs = True

    def run(self):
        while self.more_inputs:
            time.sleep(1)

    def input(self, document):
        if self.channel == None:
            # connect if necessary
            pass
        # publish
        print("publishing %s via amqp" % document.id)

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(AmqpPublishStep())
