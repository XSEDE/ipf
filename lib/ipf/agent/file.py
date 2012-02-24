
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

import logging
import os
import ConfigParser

from ipf.agent import *

logger = logging.getLogger("FilePublishingAgent")

##############################################################################################################

class FilePublishingAgent(Agent):
    def __init__(self, args={}):
        Agent.__init__(self,args)

    def run(self, docs_in=[]):
        try:
            file_name = self.config.get("publish_file","file_name")
        except ConfigParser.Error:
            logger.error("filepub.file_name not specified")
            raise AgentError("filepub.file_name not specified")

        if file_name[0] != "/":
            # relative path - from install directory
            file_name = os.path.join(home_dir,file_name)

        if docs_in == None or len(docs_in) != 1:
            logger.error("can only publish exactly one document")
            raise AgentError("can only publish exactly one document")

        file = open(file_name,"w")
        file.write(docs_in[0].body)
        file.close()

        return []
    
