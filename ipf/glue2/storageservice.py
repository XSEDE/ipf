
###############################################################################
#   Copyright 2012-2014 The University of Texas at Austin                     #
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
import datetime
import os
import re

from ipf.dt import localtzoffset
from ipf.error import StepError
from ipf.log import LogDirectoryWatcher

from . import computing_manager
from . import service
#from . import computing_share
from . import execution_environment
from ipf.step import Step
import json
#from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation

from .entity import *

#######################################################################################################################

class StorageServiceStep(Step):

    def __init__(self):
        Step.__init__(self)

    def run(self):
        serv = service.Service()
        #service.Name = "PBS"
        #service.Capability = ["executionmanagement.jobexecution",
        #                      "executionmanagement.jobdescription",
        #                      "executionmanagement.jobmanager",
        #                      "executionmanagement.executionandplanning",
        #                      "executionmanagement.reservation",
        #                      ]
        #service.Type = "ipf.PBS"
        #service.QualityLevel = "production"

#	 try:
#            self.exclude = self.params["exclude"].split(",")
#        except KeyError:
#            self.exclude = []

        service_paths = []
        try:
            paths = os.environ["SERVICEPATH"]
            service_paths.extend(paths.split(":"))
        except KeyError:
            raise StepError("didn't find environment variable SERVICEPATH")
#
        for path in service_paths:
            try:
                packages = os.listdir(path)
            except OSError:
                continue
            for name in packages:
                print("name of package is" +name)
		print("path is " +path)
                if name.startswith("."):
                    continue
                if name.endswith("~"):
                    continue
                if name.endswith(".lua"):
                    self._addService(os.path.join(path,name),path,serv)
                else:
                    self.info("calling addmodule w/ version")
                    print("calling addmodule w/ version")
                    self._addService(os.path.join(path,name),path,serv)
#
        return serv
#
    def _addService(self, path, name, serv):
#
        try:
            file = open(path)
        except IOError, e:
            self.warning("%s" % e)
            return
        text = file.read()
        file.close()
        print("in correct _addService")
        m = re.search("Name = ([^\ ]+)",text)
        if m is not None:
            serv.Name = m.group(1).strip()
	    print(serv.Name)
        else:
            self.debug("no name in "+path)
            print("no name in "+path)
        m = re.search("Type = ([^\ ]+)",text)
        if m is not None:
            serv.Type = m.group(1).strip()
	    print(serv.Type)
        else:
            self.debug("no type in "+path)
            print("no type in "+path)
        m = re.search("Version = ([^\ ]+)",text)
        if m is not None:
            serv.Version = m.group(1).strip()
	    print(serv.Version)
        else:
            self.debug("no Version in "+path)
            print("no Version in "+path)
        m = re.search("Endpoint = ([^\ ]+)",text)
        if m is not None:
            serv.Endpoint = m.group(1).strip()
	    print(serv.Endpoint)
        else:
            self.debug("no endpoint in "+path)
            print("no endpoint in "+path)
        m = re.search("Capability = ([^\ ]+)",text)
        if m is not None:
	    capability=[]
            capability.append(m.group(1).strip())
            serv.Capability = capability
        else:
            self.debug("no Capability in "+path)
            print("no capability in "+path)
        m = re.search("SupportStatus = ([^\ ]+)",text)
        if m is not None:
            serv.QualityLevel = m.group(1).strip()
        else:
            self.debug("no support status in "+path)
            print("no support status in "+path)
        m = re.search("QualityLevel = ([^\ ]+)",text)
        if m is not None:
            serv.QualityLevel = m.group(1).strip()
        else:
            self.debug("no qualitylevel in "+path)
            print("no qualitylevel in "+path)
        m = re.search("Keywords = ([^\ ]+)",text)
        if m is not None:
            serv.Extension["Keywords"] = map(str.strip,m.group(1).split(","))
        else:
            self.debug("no keywords in "+path)
            print("no keywords in "+path)
        
#######################################################################################################################
