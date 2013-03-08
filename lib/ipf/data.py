
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

import sys

from ipf.error import *

##############################################################################################################

class Data(object):
    def __init__(self, id=None):
        self.id = id         # an identifier for the content of the document - may be used when publishing
        self.source = None   # set by the engine - an identifier for the source of a document to help route it

    def __str__(self):
        return "data %s of type %s.%s" % (self.id,self.__module__,self.__class__.__name__)
    
    def getRepresentation(self, representation_name):
        pass

##############################################################################################################

class Representation(object):
    MIME_TEXT_PLAIN = "text/plain"
    MIME_TEXT_XML = "text/xml"
    MIME_APPLICATION_JSON = "application/json"

    data_cls = None    # the Data class that this class can represent

    def __init__(self, mime_type, data):
        if not isinstance(data,self.data_cls):
            raise RepresentationError("data is a %s, but must be a %s" % (data.__class__.__name__,data_cls.__name__))
        
        #self.name = self.__module__+"."+self.__class__.__name__
        self.mime_type = mime_type    # the MIME type provided by this representation
        self.data = data              # the data that is represented

    def __str__(self):
        return "representation %s of %s %s" % (self.__class__.__name__,self.data_cls.__name__,self.data.id)

    def get(self):
        raise NotImplementedError()
    
##############################################################################################################
