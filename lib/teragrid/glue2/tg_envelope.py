
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

from ipf.document import Document
from teragrid.tgagent import TeraGridAgent
from teragrid.xmlhelper import *

logger = logging.getLogger("TeraGridGlue2Agent")

##############################################################################################################

class TeraGridGlue2Agent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)

    def run(self, docs_in=[]):
        glue2 = Glue2()
        glue2.id = self._getSystemName()
        glue2.docs = docs_in
        glue2.UniqueID = "glue2."+self._getSystemName()
        return [glue2]

##############################################################################################################

class Glue2(Document):
    def __init__(self, args={}):
        Document.__init__(self)
        self.type = "teragrid.glue2.Envelope"
        self.content_type = "text/xml"
        self.docs = None
        self.UniqueID = None

    def _setBody(self, body):
        logger.info("Glue2._setBody should parse the XML...")

    def _getBody(self):
        #g2str = "<?xml version='1.0' encoding='UTF-8'?>\n"
        g2str = "<V4glue2RP xmlns='http://mds.teragrid.org/2007/02/ctss'>\n"
        g2str = g2str + "<glue2 Timestamp='"+epochToXmlDateTime(time.time())+"' UniqueID='"+self.UniqueID+"'>\n"
        for doc in self.docs:
            g2str = g2str + doc.body
        g2str = g2str + "</glue2>\n"
        g2str = g2str + "</V4glue2RP>\n"
        return g2str
        
