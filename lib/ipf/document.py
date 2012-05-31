
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

    documents = {}

    def __init__(self, id, type):
        # some identifier for the content of the document - may be used when publishing
        self.id = id
        if type in self.documents:
            raise ipf.error.DocumentError("Document class already defined for type %s" % type)
        # an identifier for the type/schema of the content
        self.type = type
        
        self.source = None         # set by the engine - an identifier for the source of a document to help route it
        self._body = None

    def __str__(self):
        dstr = "document "+str(self.id)+" of type "+str(self.type)+":\n"
        dstr = dstr + self.body
        return dstr

    # child class can override
    def _setBody(self, body):
        self._body = body

    # child class can override
    def _getBody(self):
        return self._body

    body = property(lambda self: self._getBody(),
                    lambda self, body: self._setBody(body))

    @classmethod
    def read(cls, fd=sys.stdin):

        id = None
        type = None
        source = None
        length = None

        line = fd.readline()
        while line != "":
            #print("read: '%s'" % line)
            toks = line.split(":")
            #print(toks)
            if len(toks) < 2:
                break

            key = toks[0].lstrip().strip()
            value = toks[1].lstrip().strip()

            if key == "id":
                id = value
            elif key == "type":
                type = value
            elif key == "source":
                source = value
            elif key == "length":
                length = int(value)
            else:
                logger.info("ignoring header with key "+key)
            line = fd.readline()

        if id == None:
            raise ipf.error.ReadDocumentError("document id not specified")

        if type == None:
            raise ipf.error.ReadDocumentError("document type not specified")
        if type in cls.documents:
            document = self.documents[type]()
        else:
            document = Document(id,type)

        if source == None:
            raise ipf.error.ReadDocumentError("document source not specified")
        document.source = source

        if length == None:
            raise ipf.error.ReadDocumentError("document length not specified")
        document.body = fd.read(length)
        if len(document.body) != length:
            raise ipf.error.ReadDocumentError("failed to read document content")

        return document

    def write(self, fd=sys.stdout):
        if self.id == None:
            raise ipf.error.WriteDocumentError("id is not specified")
        if self.type == None:
            raise ipf.error.WriteDocumentError("type is not specified")

        body = self.body
        if body == None:
            raise ipf.error.WriteDocumentError("body not specified")

        fd.write("id: %s\n" % self.id)
        fd.write("type: %s\n" % self.type)
        fd.write("source: %s\n" % self.source)
        fd.write("length: %d\n" % len(body))
        fd.write("\n")
        fd.write(body)
