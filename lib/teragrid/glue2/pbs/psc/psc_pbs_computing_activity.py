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
import datetime
import logging
import os
import re
import sys
import xml.sax
import xml.sax.handler
import ConfigParser

from ipf.error import *
from teragrid.glue2.computing_activity import *

logger = logging.getLogger("PscPbsJobsAgent")

##############################################################################################################

class PscPbsJobsAgent(PbsJobsAgent):
    def __init__(self, args={}):
        PbsJobsAgent.__init__(self,args)

    def run(self, docs_in=[]):
        jobs = PbsJobsAgent.run(self,docs_in)

        try:
            job_list_file = self.config.get("psc","job_list_file")
        except ConfigParser.Error:
            logger.error("psc.job_list_file not specified")
            raise AgentError("psc.job_list_file not specified")

	f = open(job_list_file,"r")
	lines = f.readlines()
	f.close()

	job_ids = []
	for line in lines[1:]:
	    toks = line.split()
	    job_ids.append(toks[0])

        for job in jobs:
            job_dict[job.LocalIDFromManager] = job

        jobs = []
	for job_id in job_ids:
            foundIt = False
            try:
                jobs.append(job_dict[job_id])
                del job_dict[job_id]
            except KeyError:
                logger.warn("didn't find PBS job "+job_id+" in job list")
        for job_id in jobs.keys():
            logger.warn("didn't find an entry in job list for PBS job "+job_id)
        return jobs


##############################################################################################################

if __name__ == "__main__":    
    agent = PscPbsJobsAgent.createFromCommandLine()
    agent.runStdinStdout()
