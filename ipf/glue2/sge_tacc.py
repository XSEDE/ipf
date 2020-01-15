
###############################################################################
#   Copyright 2011-2014 The University of Texas at Austin                     #
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

import subprocess
import logging
import os
import socket

from ipf.error import StepError

from . import sge

##############################################################################################################

class ComputingSharesStep(sge.ComputingSharesStep):

    def __init__(self):
        sge.ComputingSharesStep.__init__(self)

    def _run(self):
        queues = sge.ComputingSharesStep._run(self)

        try:
            job_policy_file = self.config.get("tacc","job_policy_file")
        except ConfigParser.Error:
            raise StepError("tacc.job_policy_file not specified")

        try:
            file = open(job_policy_file,"r")
            lines = file.readlines()
            file.close()
        except:
            raise StepError("failed to read job policy file "+job_policy_file)

        # bit of a hack, but good enough
        for line in lines:
            toks = line.split()
            if len(toks) == 0 or toks[0][0] == "#":
                continue
            if toks[0] == "max_cores_per_job" and toks[1] == "*":
                for queue in queues:
                    if queue.Name == toks[2] or toks[2] == "*":
                        queue.MaxSlotsPerJob = int(toks[3])
            if toks[0] == "max_time_per_job" and toks[1] == "*":
                for queue in queues:
                    if queue.Name == toks[2] or toks[2] == "*":
                        queue.MaxWallTime = int(toks[3])
            if toks[0] == "max_jobs_per_user" and toks[1] == "*":
                for queue in queues:
                    if queue.Name == toks[2] or toks[2] == "*":
                        queue.MaxTotalJobs = int(toks[3])

        return queues

##############################################################################################################

