
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
from teragrid.agent import TeraGridAgent

logger = logging.getLogger("EntitiesAgent")

##############################################################################################################

class EntitiesAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)

    def run(self, docs_in):
        entities = Entities()
        entities.id = self._getSystemName()
        entities.docs = docs_in
        return [entities]

##############################################################################################################

class Entities(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.Entities"
        self.content_type = "text/xml"
        self.docs = None

    def _setBody(self, body):
        logger.info("Entities._setBody should parse the XML...")

    def _getBody(self):
        #estr = "<?xml version='1.0' encoding='UTF-8'?>\n"
        estr = "  <Entities xmlns='http://info.teragrid.org/glue/2009/02/spec_2.0_r02'>\n"
        for doc in self.docs:
            estr = estr + doc._toXml("    ")
        estr = estr + "  </Entities>\n"
        return estr
        
