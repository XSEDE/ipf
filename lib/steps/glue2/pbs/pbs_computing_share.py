
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

from ipf.error import StepError

from glue2.computing_share import *

#######################################################################################################################

class PbsComputingSharesStep(ComputingSharesStep):

    def __init__(self, params):
        ComputingSharesStep.__init__(self,params)

        self.name = "glue2/pbs/computing_shares"
        self.accepts_params["qstat"] = "the path to the PBS qstat program (default 'qstat')"

    def _run(self):
        qstat = self.params.get("qstat","qstat")
        cmd = qstat + " -q -G"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qstat failed: "+output)
            raise StepError("qstat failed: "+output+"\n")

        queueStrings = output.split("\n")
        queueStrings = queueStrings[5:len(queueStrings)-2]

        queues = []
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if self._includeQueue(queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()

        (queueName,
         memoryLimitGB,
         cpuTimeLimit,
         wallTimeLimit,
         nodeLimit,
         runningJobs,
         queuedJobs,
         maxRunningJobs,
         enableDisable,
         runningStopped) = queueString.split()

        queue.Name = queueName
        queue.MappingQueue = queue.Name
        if cpuTimeLimit != "--":
            queue.MaxTotalCPUTime = self._getDuration(cpuTimeLimit)
        if wallTimeLimit != "--":
            queue.MaxWallTime = self._getDuration(wallTimeLimit)
        if nodeLimit != "--":
            queue.MaxSlotsPerJob = int(nodeLimit)
        queue.TotalJobs = 0
        if runningJobs != "--":
            queue.LocalRunningJobs = int(runningJobs)
            queue.RunningJobs = queue.LocalRunningJobs
            queue.TotalJobs = queue.TotalJobs + queue.RunningJobs
        if queuedJobs != "--":
            queue.LocalWaitingJobs = int(queuedJobs)
            queue.WaitingJobs = queue.LocalWaitingJobs
            queue.TotalJobs = queue.TotalJobs + queue.WaitingJobs
        if maxRunningJobs != "--":
            queue.MaxRunningJobs = int(maxRunningJobs)
        if enableDisable == "E":
            queue.Extension["AcceptingJobs"] = True
        else:
            queue.Extension["AcceptingJobs"] = False
        if runningStopped == "R":
            queue.Extension["RunningJobs"] = True
        else:
            queue.Extension["RunningJobs"] = False

        return queue


    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)

#######################################################################################################################
