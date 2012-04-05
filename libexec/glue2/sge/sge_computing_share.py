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

import commands
import ConfigParser

from ipf.error import *
from ipf.step import StepEngine
from teragrid.glue2.computing_share import *

#######################################################################################################################

class SgeComputingSharesStep(ComputingSharesStep):
    def __init__(self, params={}):
        ComputingSharesStep.__init__(self,params)
        self.name = "glue2/sge/computing_shares"

    def _run(self):
        return self._getQueues()

    def _getQueues(self):
        qconf = "qconf"
        try:
            qconf = self.engine.config.get("sge","qconf")
        except ConfigParser.Error:
            pass
        cmd = qconf + " -sq \**"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("qconf failed: "+output+"\n")

        queues = []
        queueStrings = output.split("\n\n")
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if includeQueue(self.engine,queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()
        queue.ComputingService = "http://"+self.resource_name+"/glue2/ComputingService"

        lines = queueString.split("\n")
        queueName = None
        for line in lines:
            if line.startswith("qname "):
                queueName = line[5:].lstrip()
                break

        queue.Name = queueName
        queue.MappingQueue = queue.Name

        for line in lines:
            if line.startswith("s_rt "):
                value = line[4:].lstrip()
                if value != "INFINITY":
                    queue.MaxWallTime = self._getDuration(value)
            if line.startswith("s_cpu "):
                value = line[5:].lstrip()
                if value != "INFINITY":
                    queue.MaxTotalCPUTime = self._getDuration(value)
            if line.startswith("h_data "):
                value = line[6:].lstrip()
                if value != "INFINITY":
                    queue.MaxMemory = self._getDuration(value)
        return queue
    
    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

#######################################################################################################################

if __name__ == "__main__":
    StepEngine(SgeComputingSharesStep())
