
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

import sys

import ipf.error

##############################################################################################################

class Document(object):
    def __init__(self):
        self.id = None             # some identifier for the content of the document - may be used when publishing
        self.type = None           # an identifier for the type/schema of the content
        self.content_type = None   # http-style content-type (the encoding of self.body)
        self._body = None

    def __str__(self):
        dstr = "document "+str(self.id)+" of type "+str(self.content_type)+":\n"
        dstr = dstr + self.body
        return dstr

    # child class can override
    def _setBody(self, body):
        self._body = body

    # child class can override
    def _getBody(self):
        return self._body

    body = property(lambda self: self._getBody(),
                    lambda self: self._setBody(body))

    def read(self, id=None, fd=sys.stdin):
        if id == None:
            self.id = fd.readline()
            if line == "":
                raise ipf.error.ReadDocumentError()
        else:
            self.id = id

        content_length = None
        line = fd.readline()
        while line != "":
            (key,value) = line.split(" :")
            if key == "Content-Type" or key == "content-type":
                self.content_type = value
            elif key == "Content-Length" or key == "content-lenth":
                content_length = int(value)
            else:
                logger.info("ignoring header with key "+key)
            line = fd.readline()

        if content_length == None:
            raise ipf.error.ReadDocumentError("didn't find content length")
        document.body = fd.read(content_length)

    def write(self, fd=sys.stdout):
        if self.id == None:
            raise ipf.error.WriteDocumentError("id is not specified")
        body = self.body
        if body == None:
            raise ipf.error.WriteDocumentError("body not specified")
        #fd.write("PUT "+self.id+"\n")
        fd.write(self.id+"\n")
        fd.write("Content-Type: "+self.content_type+"\n")
        fd.write("Content-Length: "+str(len(body))+"\n")
        fd.write("\n")
        fd.write(body)
