
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

class ResourceNameDocumentTxt(Document):
    def __init__(self, host_name):
        Document.__init__(self, host_name, "ipf/resource_name.txt")
        self.body = "%s\n" % host_name

class ResourceNameDocumentJson(Document):
    def __init__(self, host_name):
        Document.__init__(self, host_name, "ipf/resource_name.json")
        self.body = "{\"resourceName\": \"%s\"}\n" % host_name

class ResourceNameDocumentXml(Document):
    def __init__(self, host_name):
        Document.__init__(self, host_name, "ipf/resource_name.xml")
        self.body = "<ResourceName>%s</ResourceName>\n" % host_name
