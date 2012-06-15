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
import sys
import time

from ipf.step import Step

#######################################################################################################################

class AmqpPublishStep(Step):

    def __init__(self, params):
        Step.__init__(self,params)

        self.name = "ipf/publish/amqp"
        self.description = "publishes documents by via AMQP"
        self.time_out = 5
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
        # connect
        more_inputs = True
        while more_inputs:
            doc = self.input_queue.get(True)
            if doc == Step.NO_MORE_INPUTS:
                more_inputs = False
            else:
                self.info("publishing document of type %s" % doc.type)

#######################################################################################################################
