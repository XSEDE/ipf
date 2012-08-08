
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

import commands
import datetime
import os
import socket
import sys
import re
import xml.sax
import xml.sax.handler

from ipf.dt import *
from ipf.error import StepError

from glue2.log import LogFileWatcher
import glue2.computing_activity
import glue2.computing_endpoint
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
import glue2.execution_environment
from glue2.teragrid.platform import PlatformMixIn

#######################################################################################################################

class ComputingServiceStep(glue2.computing_service.ComputingServiceStep):
    def __init__(self):
        glue2.computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = glue2.computing_service.ComputingService()
        service.Name = "Nimbus"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager"
                              ]
        service.Type = "org.nimbus"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):
    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

        self._acceptParameter("nimbus_version","the Nimbus version",False)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "Nimbus"
        manager.Name = "Nimbus"
        manager.Reservation = False
        manager.BulkSubmission = True

        try:
            manager.Version = self.params["nimbus_version"]
        except KeyError:
            pass

        return manager

#######################################################################################################################

class EndpointStep(glue2.computing_endpoint.ComputingEndpointStep):
    def __init__(self):
        glue2.computing_endpoint.ComputingEndpointStep.__init__(self)

        self.description = "create ComputingEndpoints for Nimbus"
        self._acceptParameter("host_name",
                              "the name of the host the Nimbus service runs on (default is the local host)",
                              False)
        self._acceptParameter("nimbus_version","the version of Nimbus installed (optional)",False)
        self._acceptParameter("nimbus_dir","the path to the nimbus directory (optional)",False)

    def _run(self):
        try:
            host_name = self.params["host_name"]
        except KeyError:
            host_name = socket.getfqdn()

        issuer = self._getIssuer()

        endpoints = []

        endpoint = self._getEndpoint(issuer)
        endpoint.Name = "nimbus-wsrf"
        endpoint.URL = "http://%s:8443" % host_name
        endpoint.Technology = "SOAP"
        endpoint.InterfaceName = "WSRF"
        endpoints.append(endpoint)

        endpoint = self._getEndpoint(issuer)
        endpoint.Name = "nimbus-rest"
        endpoint.URL = "http://%s:8444" % host_name
        endpoint.Technology = "REST"
        endpoint.InterfaceName = "EC2"
        endpoints.append(endpoint)

        return endpoints

    def _getEndpoint(self, issuer):
        endpoint = glue2.computing_endpoint.ComputingEndpoint()
        endpoint.Capability = ["executionmanagement.jobdescription",
                           "executionmanagement.jobexecution",
                           "executionmanagement.jobmanager",
                           ]
        endpoint.Implementor = "The Nimbus Project"
        endpoint.ImplementationName = "Nimbus"
        try:
            endpoint.ImplementationVersion = self.params["nimbus_version"]
        except KeyError:
            pass
        endpoint.QualityLevel = "production"
        endpoint.IssuerCA = issuer

        return endpoint

    def _getIssuer(self):
        try:
            nimbus_dir = self.params["nimbus_dir"]
        except KeyError:
            return None

        cert_file = os.path.join(nimbus_dir,"var","hostcert.pem")
        grid_cert_info = os.path.join(nimbus_dir,"services","bin","grid-cert-info")

        os.environ["GLOBUS_LOCATION"] = os.path.join(nimbus_dir,"services")
        cmd = grid_cert_info + " -issuer -file "+cert_file
        (status, output) = commands.getstatusoutput(cmd)
        if status == 0:
            try:
                # remove the 'issuer      : ' prefix and strip off any leading and trailing whitespace
                return output[output.index(":")+1:].strip()
            except ValueError:
                self.warning("getIssuer failed to process output of grid-cert-info: %s",output)
                return None
        else:
            self.warning("getIssuer failed on grid-cert-info: %s",output)
            return None

#######################################################################################################################

# dn="/O=Auto/OU=FutureGridNimbus/CN=smithd", minutes=18000, uuid="1798eca6-3f31-4592-89d5-4d79956dc3b3", eprkey=943, creation="Jun 8, 2012 3:49:42 PM"

# CREATED: time="Jun 17, 2012 2:45:07 AM", uuid="5e2db9fa-fe87-4146-89ea-788097cedcce", eprkey=980, dn="/O=Auto/OU=FutureGridNimbus/CN=inca", requestMinutes=60, charge=60, chargeRatio=1.0, CPUCount=1, memory=1280, clientLaunchName='https://master1.futuregrid.tacc.utexas.edu:8443/head-node', network='publicnic;public;A2:AA:BB:84:F5:08;Bridged;AllocateAndConfigure;129.114.32.106;129.114.32.1;192.114.32.255;255.255.255.0;129.114.4.18;vm-106.alamo.futuregrid.org;null;null;null;null'

class NimbusActivityMixIn(object):
    def _createActivity(self, line):
        activity = glue2.computing_activity.ComputingActivity()
        activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
        
        m = re.search("eprkey=(\d+)",line)
        activity.LocalIDFromManager = m.group(1)

        try:
            m = re.search("clientLaunchName='(\S+)'",line)
            activity.Name = m.group(1)
        except AttributeError:
            pass  # not in current-reservations.txt

        try:
            m = re.search("dn=\"([^\"]+)\"",line)
            activity.Owner = m.group(1)
            m = re.search("dn=\".*CN=([^\"]+)\"",line)
            activity.LocalOwner = m.group(1)
        except AttributeError:
            pass

        try:
            m = re.search("creation=\"([^\"]+)\"",line) # current-reservations.txt
            start_str = m.group(1)
        except AttributeError:
            try:
                m = re.search("time=\"([^\"]+)\"",line) # accounting-events.txt
                start_str = m.group(1)
            except AttributeError:
                self.warning("didn't find creation time for VM in %s",line)
                start_str = None
        if start_str is not None:
            activity.StartTime = self._getDateTime(start_str)

        try:
            m = re.search("CPUCount=(\d+)",line)
            activity.RequestedSlots = int(m.group(1))
            if activity.StartTime is not None:
                usedWallTime = time.mktime(activity.CreationTime.timetuple()) - \
                               time.mktime(activity.StartTime.timetuple())
                activity.UsedTotalWallTime = usedWallTime * activity.RequestedSlots
        except AttributeError:
            pass  # cpuCount not in current-reservations.txt

        if activity.RequestedSlots is not None:
            try:
                m = re.search("minutes=(\d+)",line)             # current-reservations.txt
                activity.RequestedTotalWallTime = int(m.group(1)) * 60 * activity.RequestedSlots
            except AttributeError:
                try:
                    m = re.search("requestMinutes=(\d+)",line)  # accounting-events.txt
                    activity.RequestedTotalWallTime = int(m.group(1)) * 60 * activity.RequestedSlots
                except AttributeError:
                    self.warning("didn't find requested minutes for VM in %s",line)

        return activity

    def _getDateTime(self, dtStr):
        # Example: Jun 17, 2012 2:45:07 AM
        d = datetime.datetime.strptime(dtStr,"%b %d, %Y %I:%M:%S %p")
        return datetime.datetime(d.year,d.month,d.day,d.hour,d.minute,d.second,d.microsecond,localtzoffset())

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep, NimbusActivityMixIn):
    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("nimbus_dir","the path to the NIMBUS directory",True)

    def _run(self):
        try:
            self.nimbus_dir = self.params["nimbus_dir"]
        except KeyError:
            raise StepError("nimbus_dir parameter not specified")

        rsv_dict = self._getCurrentReservations()
        self._addAccountingInformation(rsv_dict)
        return map(self._createActivity,rsv_dict.values())

    def _getCurrentReservations(self):
        file = open(os.path.join(self.nimbus_dir,"services","var","nimbus","current-reservations.txt"),"r")
        lines = file.readlines()
        file.close()

        rsv_dict={}
        for line in lines:
            m = re.search("eprkey=(\d+)",line)
            rsv_dict[m.group(1)] = line
        return rsv_dict

    def _addAccountingInformation(self, rsv_dict):
        file = ReverseFileReader(os.path.join(self.nimbus_dir,"services","var","nimbus","accounting-events.txt"))
        found = set()
        line = file.readline()
        while line is not None and len(found) < len(rsv_dict):
            if line.startswith("CREATED: "):
                try:
                    m = re.search("eprkey=(\d+)",line)
                    eprkey = m.group(1)
                except AttributeError:
                    self.warning("didn't find eprkey in %s",line)
                    continue
                if eprkey in rsv_dict:
                    rsv_dict[eprkey] = line
                    found.add(eprkey)
            elif line.startswith("REMOVED: "):
                # pick up any VMs that stopped in the last 10 mins?
                pass
            else:
                self.info("unhandled accounting log entry: %s",line)
            line = file.readline()
        file.close()

#######################################################################################################################

class ReverseFileReader(object):
    def __init__(self, path):
        self.file = open(path,"r")
        self.read_size = 1024
        self.buffer = ""
        self.file.seek(0,os.SEEK_END)
        self.pos = self.file.tell()

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.buffer = ""

    def readline(self):
        try:
            start_pos = self.buffer.rindex("\n",0,len(self.buffer)-1)
            line = self.buffer[start_pos+1:]
            self.buffer = self.buffer[:start_pos+1]
            return line
        except ValueError:
            if self.pos == 0:
                return ""
            self._readMore()
            return self.readline()

    def _readMore(self):
        if self.pos < self.read_size:
            read_size = self.pos
            self.pos = 0
        else:
            read_size = self.read_size
            self.pos = self.pos - self.read_size
        self.file.seek(self.pos)
        self.buffer = self.file.read(read_size) + self.buffer

#######################################################################################################################

class ComputingActivityUpdateStep(glue2.computing_activity.ComputingActivityUpdateStep, NimbusActivityMixIn):
    def __init__(self):
        glue2.computing_activity.ComputingActivityUpdateStep.__init__(self)

        self._acceptParameter("nimbus_dir","the path to the NIMBUS directory",True)

    def _run(self):
        self.info("running")
        try:
            nimbus_dir = self.params["nimbus_dir"]
        except KeyError:
            raise StepError("nimbus_dir parameter not specified")

        watcher = LogFileWatcher(self._logEntry,
                                 os.path.join(nimbus_dir,"services","var","nimbus","accounting-events.txt"))
        watcher.run()

    def _logEntry(self, log_file_name, entry):
        activity = self._createActivity(entry)
        if activity.Queue is None or self._includeQueue(activity.Queue):
            self.output(activity)

#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):
    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

    def _run(self):
        return []

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep):
    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)

        self._acceptParameter("nimbus_dir",
                              "the path to the Nimbus directory (optional - for specifying location of nimbus-nodes command)",
                              False)
        self._acceptParameter("cores_per_node","the number of processing cores per node",False)

    def _run(self):
        try:
            nimbus_nodes = os.path.join(self.params["nimbus_dir"],"bin","nimbus-nodes")
        except KeyError:
            nimbus_nodes = "nimbus-nodes"

        cmd = nimbus_nodes + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("nimbus-nodes failed: "+output+"\n")

        nodeStrings = output.split("\n\n")
        return map(self._getNode,nodeStrings)

    def _getNode(self, nodeString):
        lines = nodeString.split("\n")

        node = glue2.execution_environment.ExecutionEnvironment()
        node.TotalInstances = 1
        try:
            node.LogicalCPUs = self.params["cores_per_node"]
        except KeyError:
            pass

        for line in lines:
            if "hostname" in line:
                pass
            elif "pool" in line:
                node.Name = line.split()[2]
            elif "memory available" in line:
                available_memory = int(line.split()[3])
            elif "memory" in line:
                node.MainMemorySize = int(line.split()[2])
            elif "in_use" in line:
                if line.split()[2] == "true":
                    # use available memory to decide if the node is fully used
                    if available_memory == 0:
                        node.UsedInstances = 1
                        node.Extension["PartiallyUsedInstances"] = 0
                    else:
                        node.UsedInstances = 0
                        node.Extension["PartiallyUsedInstances"] = 1
                else:
                    node.UsedInstances = 0
                    node.Extension["PartiallyUsedInstances"] = 0
            elif "active" in line:
                if line.split()[2] == "true":
                    node.UnavailableInstances = 0
                else:
                    node.UnavailableInstances = 1
        return node

#######################################################################################################################
