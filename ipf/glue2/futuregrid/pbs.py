
###############################################################################
#   Copyright 2012-2014 The University of Texas at Austin                     #
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

from .. import computing_activity
from .. import pbs

#######################################################################################################################

class ComputingActivitiesStep(pbs.ComputingActivitiesStep):

    def __init__(self):
        pbs.ComputingActivitiesStep.__init__(self)

    def _run(self):
        jobs = pbs.ComputingActivitiesStep._run(self)
        for job in jobs:
            # on FutureGrid, the local unix username is the same as their FutureGrid portal username
            job.Owner = job.LocalOwner
        return jobs

#######################################################################################################################

class ComputingActivityUpdateStep(pbs.ComputingActivityUpdateStep):

    def __init__(self):
        pbs.ComputingActivityUpdateStep.__init__(self)

    def output(self, activity):
        activity.Owner = activity.LocalOwner
        computing_activity.ComputingActivityUpdateStep.output(self,activity)

#######################################################################################################################
