
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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


import glue2.computing_activity

##############################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):

    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self.requires.append(glue2.computing_activity.ComputingActivities)

        self._acceptParameter("query_priority",
                              "the path to the Catalina query_priority program (default 'query_priority')",
                              False)


    def _run(self):
        query_priority = self.params.get("query_priority","query_priority")

        jobs = self._getInput(glue2.computing_activity.ComputingActivities).activities

        job_map = {}
        for job in jobs:
            job_map[job.LocalIDFromManager] = job

        self.debug("running "+query_priority)
        status, output = commands.getstatusoutput(query_priority)
        if status != 0:
            raise StepError("'%s' failed: %s\n" % (cmd,output))

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
            priority = int(toks[1])
            try:
                job_map[id].Extension["Priority"] = priority
                if state == "held":
                    if job_map[id].State == glue2.computing_activity.ComputingActivity.STATE_PENDING:
                        job_map[id].State = glue2.computing_activity.ComputingActivity.STATE_HELD
            except KeyError:
                self.warning("didn't find job %s in resource manager jobs")

        jobs = sorted(jobs,key=self._jobPriority)
        jobs = sorted(jobs,key=self._jobStateKey)

        return jobs

    def _jobPriority(self, job):
        try:
            return -job.Extension["Priority"]
        except KeyError:
            return 0

    def _jobStateKey(self, job):
        if job.State == glue2.computing_activity.ComputingActivity.STATE_RUNNING:
            return 1
        if job.State == glue2.computing_activity.ComputingActivity.STATE_STARTING:
            return 2
        if job.State == glue2.computing_activity.ComputingActivity.STATE_SUSPENDED:
            return 3
        if job.State == glue2.computing_activity.ComputingActivity.STATE_PENDING:
            return 4
        if job.State == glue2.computing_activity.ComputingActivity.STATE_HELD:
            return 5
        if job.State == glue2.computing_activity.ComputingActivity.STATE_FINISHING:
            return 6
        if job.State == glue2.computing_activity.ComputingActivity.STATE_TERMINATING:
            return 7
        if job.State == glue2.computing_activity.ComputingActivity.STATE_FINISHED:
            return 8
        if job.State == glue2.computing_activity.ComputingActivity.STATE_TERMINATED:
            return 9
        if job.State == glue2.computing_activity.ComputingActivity.STATE_FAILED:
            return 10
        if job.State == glue2.computing_activity.ComputingActivity.STATE_UNKNOWN:
            return 11
        return 12  # above should be all of them, but...
