
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

from ipf.document import Document

class SiteNameDocumentTxt(Document):
    def __init__(self, site_name):
        Document.__init__(self, site_name, "ipf/site_name.txt")
        self.body = "%s\n" % site_name

class SiteNameDocumentJson(Document):
    def __init__(self, site_name):
        Document.__init__(self, site_name, "ipf/site_name.json")
        self.body = "{\"siteName\": \"%s\"}\n" % site_name

class SiteNameDocumentXml(Document):
    def __init__(self, site_name):
        Document.__init__(self, site_name, "ipf/site_name.xml")
        self.body = "<SiteName>%s</SiteName>\n" % site_name
