
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
        glue2.resourceId = self._getSystemName()
        glue2.siteId = glue2.resourceId[glue2.resourceId.find(".")+1:]
        glue2.uniqueId = "glue2."+self._getSystemName()
        return [glue2]

##############################################################################################################

class Glue2(Document):
    def __init__(self, args={}):
        Document.__init__(self)
        self.type = "teragrid.glue2.Envelope"
        self.content_type = "text/xml"
        self.uniqueId = None
        self.resourceId = None
        self.siteId = None
        self.docs = None

    def _setBody(self, body):
        logger.info("Glue2._setBody should parse the XML...")

    def _getBody(self):
        #gstr = "<?xml version='1.0' encoding='UTF-8'?>\n"
        #gstr = "<V4glue2RP xmlns='http://mds.teragrid.org/2007/02/ctss'>\n"
        gstr = "<glue2 xmlns='http://info.teragrid.org/2011/05/ctss'\n"
        gstr = gstr + "       Timestamp='%s'\n" % (epochToXmlDateTime(time.time()))
        gstr = gstr + "       UniqueID='%s'>\n" % (self.uniqueId)
        gstr = gstr + "  <ResourceID>%s</ResourceID>\n" % (self.resourceId)
        gstr = gstr + "  <SiteID>%s</SiteID>\n" % (self.siteId)
        for doc in self.docs:
            gstr = gstr + doc.body
        gstr = gstr + "</glue2>\n"
        #gstr = gstr + "</V4glue2RP>\n"
        return gstr

##############################################################################################################

class MdsEnvelopeAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)

    def run(self, docs_in=[]):
        mds = MdsEnvelope();
        mds.docs = docs_in
        return [mds]

##############################################################################################################

class MdsEnvelope(Document):
    def __init__(self, args={}):
        Document.__init__(self)
        self.type = "teragrid.glue2.Envelope"
        self.content_type = "text/xml"
        self.docs = []

    def _setBody(self, body):
        logger.info("MdsEnvelope._setBody should parse the XML...")

    def _getBody(self):
        mstr = "<V4glue2RP xmlns='http://mds.teragrid.org/2007/02/ctss'>\n"
        for doc in self.docs:
            mstr = mstr + doc.body
        mstr = mstr + "</V4glue2RP>\n"
        return mstr
        
