
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
import os
import socket
import ConfigParser

from ipf.agent import *

##############################################################################################################

class TeraGridAgent(Agent):
    def __init__(self, args={}):
        Agent.__init__(self,args)
        self.system_name = None

    # may not be needed
    #def _getHostName(self):
    #    if self.host_name == None:
    #        self._setHostName()
    #    return self.host_name

    def _setHostName(self):
        try:
            self.host_name = self.config.get("default","hostname")
            return
        except ConfigParser.Error:
            pass

        self.host_name = os.environ.get("GLOBUS_HOSTNAME")
        if self.host_name != None:
            return

        self.host_name = socket.gethostname()

    def _getSystemName(self):
        if self.system_name == None:
            self._setSystemName()
        return self.system_name
    
    def _setSystemName(self):
        try:
            self.system_name = self.config.get("teragrid","system_name")
            return
        except ConfigParser.Error:
            pass
        tg_whereami = "tgwhereami"
        try:
            tg_whereami = self.config.get("teragrid","tgwhereami")
        except ConfigParser.Error:
            pass
        (status, output) = commands.getstatusoutput(tg_whereami)
        if status == 0:
            self.system_name = output
            return
        # don't fall back to hostname stuff
        raise AgentError("execution of '"+tg_whereami+"' failed: "+output)
        #self.system_name = self._getHostName()
