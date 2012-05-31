#!/usr/bin/env python

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

import commands
import copy
import datetime
import os
import re
import xml.sax
import xml.sax.handler

from ipf.error import StepError

from glue2.execution_environment import *

#######################################################################################################################

# the Queues argument is defined in ComputingActivity

#######################################################################################################################

class SgeExecutionEnvironmentsStep(ExecutionEnvironmentsStep):
    name = "glue2/sge/execution_environments"
    accepts_params = copy.copy(ExecutionEnvironmentsStep.accepts_params)
    accepts_params["qhost"] = "the path to the SGE qhost program (default 'qhost')"

    def __init__(self, params):
        ExecutionEnvironmentsStep.__init__(self,params)

    def _run(self):
        try:
            qhost = self.params["qhost"]
        except KeyError:
            qhost = "qhost"

        cmd = qhost + " -xml -q"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            self.error("qhost failed: "+output+"\n")
            raise StepError("qhost failed: "+output+"\n")

        handler = HostsHandler(self)
        xml.sax.parseString(output,handler)

        hosts = []
        for host in handler.hosts:
            if self._goodHost(host):
                hosts.append(host)

        return hosts

#######################################################################################################################

class HostsHandler(xml.sax.handler.ContentHandler):

    def __init__(self, step):
        self.step = step
        self.cur_host = None
        self.hosts = []
        self.cur_time = time.time()
        self.hostvalue_name = None
        self.text = ""

    def startDocument(self):
        pass

    def endDocument(self):
        if self.cur_host != None and self._goodHost(self.cur_host):
            self.hosts.append(self.cur_host)

    def startElement(self, name, attrs):
        if name == "host":
            self.cur_host = ExecutionEnvironment()
            self.cur_host.Name = attrs.getValue("name")
            self.cur_host.TotalInstances = 1
            self.cur_host.ComputingManager = "http://"+self.step.resource_name+"/glue2/ComputingManager"
        elif name == "queue":
            self.cur_host.ComputingShare.append(attrs.getValue("name")) # LocalID
        elif name == "hostvalue":
            self.hostvalue_name = attrs.getValue("name")
        
    def endElement(self, name):
        if name == "host":
            if self.cur_host.PhysicalCPUs != None:
                self.hosts.append(self.cur_host)
            self.cur_host = None

        self.text = self.text.lstrip().rstrip()
        if name == "hostvalue":
            if self.hostvalue_name == "arch_string":
                # SGE does some unknown crazy stuff to get their arch string. Just use the defaults.
                pass
            elif self.hostvalue_name == "num_proc":
                if self.text != "-":
                    self.cur_host.PhysicalCPUs = int(self.text)
                    self.cur_host.LogicalCPUs = self.cur_host.PhysicalCPUs  # don't have enough info for something else
            elif self.hostvalue_name == "load_avg":
                if self.text == "-":
                    self.cur_host.UsedInstances = 0
                    self.cur_host.UnavailableInstances = 1
                else:
                    load = float(self.text)
                    if load > float(self.cur_host.PhysicalCPUs)/2:
                        self.cur_host.Extension["UsedAverageLoad"] = load
                        self.cur_host.UsedInstances = 1
                        self.cur_host.UnavailableInstances = 0
                    else:
                        self.cur_host.Extension["AvailableAverageLoad"] = load
                        self.cur_host.UsedInstances = 0
                        self.cur_host.UnavailableInstances = 0
            elif self.hostvalue_name == "mem_total":
                if self.text != "-":
                    units = self.text[len(self.text)-1:]    # 'M' or 'G'
                    memSize = float(self.text[:len(self.text)-1])
                    if units == "G":
                        self.cur_host.MainMemorySize = int(memSize * 1024)
                    elif units == "M":
                        self.cur_host.MainMemorySize = int(memSize)
                    else:
                        self.step.warning("couldn't handle memory units of '"+units+"'")
            elif self.hostvalue_name == "mem_used":
                pass
            elif self.hostvalue_name == "swap_total":
                pass
            elif self.hostvalue_name == "swap_used":
                pass
            self.hostvalue_name = None
        self.text = ""

    def characters(self, ch):
        # all of the text for an element may not come at once
        self.text = self.text + ch
        
#######################################################################################################################
