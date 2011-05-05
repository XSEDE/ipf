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
import datetime
import logging
import os
import re
import sys
import xml.sax
import xml.sax.handler
import ConfigParser

from ipf.error import *
from teragrid.glue2.computing_activity import includeQueue
from teragrid.glue2.execution_environment import *

logger = logging.getLogger("SgeExecutionEnvironment")

##############################################################################################################

# the Queues argument is defined in ComputingActivity

##############################################################################################################

class SgeExecutionEnvironmentsAgent(ExecutionEnvironmentsAgent):
    def __init__(self, args={}):
        ExecutionEnvironmentsAgent.__init__(self)
        self.name = "teragrid.glue2.SgeExecutionEnvironment"

    def run(self, docs_in=[]):
        logger.info("running")

        for doc in docs_in:
            logger.warn("ignoring document "+doc.id)

        qhost = "qhost"
        try:
            qhost = self.config.get("sge","qhost")
        except ConfigParser.Error:
            pass

        cmd = qhost + " -xml -q"
        logger.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            logger.error("qhost failed: "+output)
            raise AgentError("qhost failed: "+output+"\n")

        handler = HostsHandler(self._getSystemName())
        xml.sax.parseString(output,handler)

        hosts = []
        for host in handler.hosts:
            if self._goodHost(host):
                hosts.append(host)

        host_groups = []
        for host in hosts:
            for host_group in host_groups:
                if host.sameHostGroup(host_group):
                    host_group.TotalInstances = host_group.TotalInstances + host.TotalInstances
                    host_group.UsedInstances = host_group.UsedInstances + host.UsedInstances
                    host_group.UnavailableInstances = host_group.UnavailableInstances + host.UnavailableInstances
                    host = None
                    break
            if host != None:
                host_groups.append(host)

        for index in range(0,len(host_groups)):
            host_groups[index].Name = "NodeType" + str(index+1)
            host_groups[index].ID = "http://"+self._getSystemName()+"/glue2/ExecutionEnvironment/"+ \
                                    host_groups[index].Name

        for host_group in host_groups:
            host_group.id = host_group.Name+"."+self._getSystemName()

        return host_groups

class HostsHandler(xml.sax.handler.ContentHandler):

    def __init__(self, system_name):
        self.system_name = system_name
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
            self.cur_host.ComputingManager = "http://"+self.system_name+"/glue2/ComputingManager/SGE"
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
                        self.cur_host.UsedInstances = 1
                        self.cur_host.UnavailableInstances = 0
                    else:
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
                        logger.warn("couldn't handle memory units of '"+units+"'")
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
        
##############################################################################################################

if __name__ == "__main__":    
    agent = SgeExecutionEnvironmentsAgent.createFromCommandLine()
    agent.runStdinStdout()
