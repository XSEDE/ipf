
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

import commands
import re
import sys

from ipf.error import StepError
from . import computing_activity

##############################################################################################################

class ComputingActivitiesStep(computing_activity.ComputingActivitiesStep):

    def __init__(self):
        computing_activity.ComputingActivitiesStep.__init__(self)

        self.requires.append(computing_activity.ComputingActivities)

        self._acceptParameter("query_priority",
                              "the path to the Catalina query_priority program (default 'query_priority')",
                              False)


    def _run(self):
        query_priority = self.params.get("query_priority","query_priority")

        jobs = self._getInput(computing_activity.ComputingActivities).activities

        job_map = {}
        for job in jobs:
            job_map[job.LocalIDFromManager] = job

        self.debug("running "+query_priority)
        status, output = commands.getstatusoutput(query_priority)
        if status != 0:
            raise StepError("'%s' failed: %s\n" % (query_priority,output))

        state = None
        for line in output.splitlines():
            if "IDLE:" in line:
                state = "pending"
                continue
            if "NON-QUEUED:" in line:
                state = "held"
                continue
            if state is None:
                continue
            toks = line.split()
            id = toks[0].split(".")[0] # remove submit host, if one is included
            if toks[1].endswith("*"):
                # a job had this priority: 100000000000000000000000000010*
                # and was the highest priority job, so:
                priority = sys.maxint
            else:
                priority = int(toks[1])
            try:
                # torque qstat shows a single JOB_ID[] for a job array, but catalina has multiple JOB_ID[##]
                m = re.search("(\S+)\[\d+\]",id)
                if m is not None:
                    id = m.group(1) + "[]"

                job_map[id].Extension["Priority"] = priority
                if state == "held":
                    if job_map[id].State[0] == computing_activity.ComputingActivity.STATE_PENDING:
                        job_map[id].State[0] = computing_activity.ComputingActivity.STATE_HELD
            except KeyError:
                self.warning("didn't find job %s in resource manager jobs",id)


        jobs = sorted(jobs,key=self._jobPriority)
        jobs = sorted(jobs,key=self._jobStateKey)

        return jobs

    def _jobPriority(self, job):
        try:
            return -job.Extension["Priority"]
        except KeyError:
            return 0
