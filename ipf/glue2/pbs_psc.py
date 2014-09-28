
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

import copy

from ipf.error import StepError

from . import pbs

#######################################################################################################################

class ComputingActivitiesStep(pbs.ComputingActivitiesStep):
    def __init__(self):
        pbs.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("job_list_file",
                              "the path to the PSC file containing the list of jobs in schedule order",
                              True)

    def _run(self):
        self.info("running")
        jobs = pbs.ComputingActivitiesStep._run(self)

        try:
            job_list_file = self.params["job_list_file"]
        except KeyError:
            raise StepError("job_list_file not specified")

        try:
            f = open(job_list_file,"r")
            lines = f.readlines()
            f.close()
        except IOError, e:
            raise StepError("couldn't read job list from file "+job_list_file)

	job_ids = []
	for line in lines[1:]:
	    toks = line.split()
	    job_ids.append(toks[0])

        job_dict = {}
        for job in jobs:
            job_dict[job.LocalIDFromManager] = job

        jobs = []
	for job_id in job_ids:
            try:
                jobs.append(job_dict[job_id])
                del job_dict[job_id]
            except KeyError:
                self.warning("didn't find job "+job_id+" in job list")
        for job_id in job_dict.keys():
            self.warning("didn't find an entry in job list for PBS job "+job_id)
        return jobs

#######################################################################################################################
