
###############################################################################
#   Copyright 2011,2012 The University of Texas at Austin                     #
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

import platform
import socket

from ipf.data import Data, Representation
from ipf.error import StepError
from ipf.step import Step
from ipf.sysinfo import ResourceName

#######################################################################################################################

class ReadFileStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces the contents of a file with an assigned id"
        self.time_out = 5
        self.requires = [ResourceName]      # Used as the data 'id' and the Amqp routing key
        self.produces = [FileContents]
        self._acceptParameter("path","a file path to read",False)
        self._acceptParameter("verify","what format to verify file contents",False)

    def run(self):
        try:
            path = self.params["path"]
        except KeyError:
            raise StepError("file path not specified")
        try:
            format = self.params["format"].lower()
        except KeyError:
            format = None
        id = self._getInput(ResourceName).resource_name
        if format:
            parms = {'format': format}
        else:
            parms = {}
 
        self._output(FileContents(path, id, **parms))

#######################################################################################################################

class FileContents(Data):
    def __init__(self, path, id, format=None):
        Data.__init__(self, path)
        self.path = path
        self.id = id
        self.format = format
        self.contents = None
        try:
            with open(self.path,"r") as file:
               self.contents = file.read()
        except IOError as e:
            raise IOError("Error '%s' reading '%s'" % (e, self.path))

        if self.format:
            if self.format == 'json':
                import json
                try:
                    parsed = json.loads(self.contents)
                except:
                    raise ValueError("File contents failed json verify")
            else:
                raise ValueError("Verify format '%s' not supported"% (self.format))

#######################################################################################################################

class FileContentsRaw(Representation):
    data_cls = FileContents

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.contents

class FileContentsID(Representation):
    data_cls = FileContents

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.id
#######################################################################################################################
