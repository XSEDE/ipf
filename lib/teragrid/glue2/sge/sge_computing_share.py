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
import logging
import os
import socket
import sys

from ipf.error import *
from teragrid.glue2.computing_share import *
from teragrid.glue2.computing_activity import *

logger = logging.getLogger("SgeQueuesAgent")

##############################################################################################################

class SgeQueuesAgent(ComputingSharesAgent):
    def __init__(self, args={}):
        ComputingSharesAgent.__init__(self,args)
        self.name = "teragrid.glue2.SgeQueuesAgent"
        # ComputingActivity can't parse XML yet
        #self._doc_class["teragrid/glue2/ComputingActivity"] = ComputingActivity

    def run(self, docs_in=[]):
        logger.info("running")
        queues = self._getQueues()

        activities = []
        for doc in docs_in:
            if doc.type == "teragrid.glue2.ComputingActivity":
                activities.append(doc)
            else:
                logger.warn("ignoring document of type "+doc.type)
        self._addActivities(activities,queues)

        for queue in queues:
            queue.id = queue.MappingQueue+"."+self._getSystemName()

        return queues

    def _getQueues(self):
        qconf = "qconf"
        try:
            qconf = self.config.get("sge","qconf")
        except ConfigParser.Error:
            pass
        cmd = qconf + " -sq \**"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("qconf failed: "+output)
            raise AgentError("qconf failed: "+output+"\n")

        queues = []
        queueStrings = output.split("\n\n")
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if includeQueue(self.config,queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()
        queue.ComputingService = "http://"+self._getSystemName()+"/glue2/ComputingService"

        lines = queueString.split("\n")
        queueName = None
        for line in lines:
            if line.startswith("qname "):
                queueName = line[5:].lstrip()
                break

        queue.Name = queueName
        queue.MappingQueue = queue.Name
        queue.ID = "http://"+self._getSystemName()+"/glue2/ComputingShare/"+queue.Name

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

##############################################################################################################

if __name__ == "__main__":
    agent = SgeQueuesAgent.createFromCommandLine()
    agent.runStdinStdout()
