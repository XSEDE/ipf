
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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

import glue2.computing_activity
import glue2.pbs

#######################################################################################################################

class ComputingActivitiesStep(glue2.pbs.ComputingActivitiesStep):

    def __init__(self):
        glue2.pbs.ComputingActivitiesStep.__init__(self)

    def _run(self):
        jobs = glue2.pbs.ComputingActivitiesStep._run(self)
        for job in jobs:
            # on FutureGrid, the local unix username is the same as their FutureGrid portal username
            job.Owner = job.LocalOwner
        return jobs

#######################################################################################################################

class ComputingActivityUpdateStep(glue2.pbs.ComputingActivityUpdateStep):

    def __init__(self):
        glue2.pbs.ComputingActivityUpdateStep.__init__(self)

    def output(self, activity):
        activity.Owner = activity.LocalOwner
        glue2.computing_activity.ComputingActivityUpdateStep.output(self,activity)

#######################################################################################################################
