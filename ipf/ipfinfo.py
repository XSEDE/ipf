
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
import pkg_resources
import os
import json

from ipf.data import Data, Representation
from ipf.error import StepError
from ipf.step import Step
from ipf.paths import IPF_PARENT_PATH, IPF_ETC_PATH, IPF_WORKFLOW_PATHS, IPF_VAR_PATH
from ipf.sysinfo import ResourceName

#######################################################################################################################

class IPFVersionStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces an IPF Version document using the pkg_resources version"
        self.time_out = 5
        self.produces = [IPFVersion]
        self._acceptParameter("ipf_version","a hard coded version number",False)

    def run(self):
        try:
            ipf_version = self.params["ipf_version"]
        except KeyError:
            try:
                ipf_version = pkg_resources.get_distribution("IPF").version
            except:
                ipf_version = "unknown"

        self._output(IPFVersion(ipf_version))

#######################################################################################################################

class IPFVersion(Data):
    def __init__(self, ipf_version):
        Data.__init__(self,ipf_version)
        self.ipf_version = ipf_version

#######################################################################################################################

class IPFVersionTxt(Representation):
    data_cls = IPFVersion

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.ipf_version

class IPFVersionJson(Representation):
    data_cls = IPFVersion

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return "{\"IPFVersion\": \"%s\"}\n" % self.data.ipf_version

class IPFVersionXml(Representation):
    data_cls = IPFVersion

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return "<IPFVersion>%s</IPFVersion>\n" % self.data.ipf_version

#######################################################################################################################

class SiteNameStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces a site name document using the fully qualified domain name of the host"
        self.time_out = 5
        self.produces = [SiteName]
        self._acceptParameter("site_name","a hard coded site name",False)
        
    def run(self):
        try:
            site_name = self.params["site_name"]
        except KeyError:
            host_name = socket.getfqdn()
            # assumes that the site name is all except first component
            try:
                index = host_name.index(".") + 1
            except ValueError:
                raise StepError("host name does not appear to be fully qualified")
            site_name = host_name[index:]

        self._output(SiteName(site_name))

#######################################################################################################################

class SiteName(Data):
    def __init__(self, site_name):
        Data.__init__(self,site_name)
        self.site_name = site_name

#######################################################################################################################

class SiteNameTxt(Representation):
    data_cls = SiteName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.site_name

class SiteNameJson(Representation):
    data_cls = SiteName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_Application_JSON,data)

    def get(self):
        return "{\"siteName\": \"%s\"}\n" % self.data.site_name

class SiteNameXml(Representation):
    data_cls = SiteName

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return "<SiteName>%s</SiteName>\n" % self.data.site_name

#######################################################################################################################

class IPFWorkflowsStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "Produces a workflows list."
        self.time_out = 10
        self.requires = [IPFVersion]
        self.produces = [IPFWorkflows]
        self._acceptParameter("workflows","A hard-coded workflows list",False)

    def run(self):
        ipf_version = self._getInput(IPFVersion).ipf_version
        try:
            plat = self.params["platform"]
        except KeyError:
            self._output(IPFWorkflows(ipf_version,self._run()))
        else:
            self._output(IPFWorkflows(ipf_version,plat))

    def _run(self):

        defined_workflows = []
        if os.path.join(IPF_ETC_PATH,"workflow/glue2") not in IPF_WORKFLOW_PATHS:
            IPF_WORKFLOW_PATHS.append(os.path.join(IPF_ETC_PATH,"workflow/glue2"))

	    for workflow_dir in IPF_WORKFLOW_PATHS:
	        workflow_files = os.listdir(workflow_dir)
            #defined_workflows.append(workflow_files)
            workflow_info = {}
            for workflowfile in workflow_files:
                with open(os.path.join(workflow_dir,workflowfile)) as json_data:
                    d = json.load(json_data)
                info_file = ""
                for step in d["steps"]:
                    if step["name"] == "ipf.publish.FileStep":
                       info_file = step["params"]["path"] 
                try:
                    if info_file:
                        timestamp = os.path.getmtime(os.path.join(IPF_VAR_PATH,info_file))
                    else:
                        timestamp = ""
                except OSError:
                    timestamp = ""
                workflow_info = json.dumps({"name": d["name"], "info_file": info_file, "timestamp": timestamp}) 
                defined_workflows.append(workflow_info)
                
		
        return defined_workflows
        #return IPF_WORKFLOW_PATHS

#######################################################################################################################

class IPFWorkflows(Data):
    def __init__(self, id, workflows):
        Data.__init__(self,id)
        self.workflows = workflows

    def __str__(self):
        return "%s" % self.workflows

#######################################################################################################################

class IPFWorkflowsTxt(Representation):
    data_cls = IPFWorkflows

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return self.data.workflows

#######################################################################################################################

class IPFInformationStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.description = "produces a document with basic information about a host"
        self.time_out = 5
        self.requires = [IPFVersion,IPFWorkflows,ResourceName]
        self.produces = [IPFInformation]

    def run(self):
        self._output(IPFInformation(self._getInput(IPFVersion).ipf_version,
                                       self._getInput(IPFWorkflows).workflows,
                                       self._getInput(ResourceName).resource_name))


#######################################################################################################################

class IPFInformation(Data):
    def __init__(self, ipf_version, workflows, resource_name):
        Data.__init__(self,ipf_version)
        self.ipf_version = ipf_version
        self.workflows = workflows
        self.resource_name = resource_name

#######################################################################################################################

class IPFInformationTxt(Representation):
    data_cls = IPFInformation

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        return "IPF version %s installed at %s on %s is running the workflows: %s\n" % (self.data.ipf_version,IPF_PARENT_PATH,self.data.resource_name,self.data.workflows)

#######################################################################################################################

class IPFInformationJson(Representation):
    data_cls = IPFInformation

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_PLAIN,data)

    def get(self):
        #return "IPF version %s installed at %s is running the workflows: %s\n" % (self.data.ipf_version,IPF_PARENT_PATH,self.data.workflows)
        return json.dumps({"IPFVersion": self.data.ipf_version, "Location": IPF_PARENT_PATH, "hostname": self.data.resource_name, "workflows": self.data.workflows})

#######################################################################################################################