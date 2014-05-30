
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
from ipf.log import LogFileWatcher

import glue2.computing_activity
import glue2.computing_endpoint
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
import glue2.execution_environment

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

class ComputingEndpointStep(glue2.computing_endpoint.ComputingEndpointStep):
    def __init__(self):
        glue2.computing_endpoint.ComputingEndpointStep.__init__(self)

        self.description = "create ComputingEndpoints for Nimbus"
        self._acceptParameter("host_name",
                              "the name of the host the Nimbus service runs on (default is the local host)",
                              False)
        self._acceptParameter("wsrf_port", "the port number Nimbus listens on for SOAP/WSRF requests (default 8443)",
                              False)
        self._acceptParameter("rest_port", "the port number Nimbus listens on for REST/EC2 requests (default 8444)",
                              False)
        self._acceptParameter("nimbus_version","the version of Nimbus installed (optional)",False)
        self._acceptParameter("nimbus_dir","the path to the nimbus directory (optional)",False)
        self._acceptParameter("openssl","the path to openssl program (default 'openssl')",False)

    def _run(self):
        host_name = self.params.get("host_name",socket.getfqdn())
        wsrf_port = self.params.get("wsrf_port",8443)
        rest_port = self.params.get("rest_port",8444)

        issuer = self._getIssuer()

        endpoints = []

        endpoint = self._getEndpoint(issuer)
        endpoint.Name = "nimbus-wsrf"
        endpoint.URL = "http://%s:%d" % (host_name,wsrf_port)
        endpoint.Technology = "SOAP"
        endpoint.InterfaceName = "WSRF"
        endpoints.append(endpoint)

        endpoint = self._getEndpoint(issuer)
        endpoint.Name = "nimbus-rest"
        endpoint.URL = "http://%s:%d" % (host_name,rest_port)
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
        try:
            openssl = self.params["openssl"]
        except KeyError:
            openssl = "openssl"

        cert_file = os.path.join(nimbus_dir,"var","hostcert.pem")
        cmd = openssl+" x509 -in "+cert_file+" -issuer -noout"
        (status, output) = commands.getstatusoutput(cmd)
        if status == 0:
            try:
                # remove the 'issuer= ' prefix
                return output[8:]
            except ValueError:
                self.warning("getIssuer failed to process output of openssl: %s",output)
                return None
        else:
            self.warning("getIssuer failed on openssl: %s",output)
            return None

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep):
    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)

        self._acceptParameter("nimbus_dir","the path to the NIMBUS directory",True)

    def _run(self):
        try:
            self.nimbus_dir = self.params["nimbus_dir"]
        except KeyError:
            raise StepError("nimbus_dir parameter not specified")

        try:
            return self._fromNimbusAdmin()
        except StepError, e:
            # probably an older Nimbus version without the nimbus-admin command
            # don't bother to pull node assignments out of services.log
            self.info("getting activities from current-reservations.txt instead of nimbus-admin: %s",str(e))
            return self._fromCurrentReservations()

    def _fromNimbusAdmin(self):
        try:
            nimbus_admin = os.path.join(self.params["nimbus_dir"],"bin","nimbus-admin")
        except KeyError:
            nimbus_admin = "nimbus-admin"

        cmd = nimbus_admin + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("nimbus-admin failed: "+output+"\n")

        vm_strings = output.split("\n\n")
        return map(self._activityFromAdmin,vm_strings)

    def _activityFromAdmin(self, vm_string):
        activity = glue2.computing_activity.ComputingActivity()
        for line in vm_string.split("\n"):
            if line.startswith("id"):
                activity.LocalIDFromManager = line[14:]
            elif line.startswith("node"):
                activity.ExecutionNode = [line[14:]]
            elif line.startswith("creator"):
                activity.LocalOwner = line[14:]  # a Distinguished Name
            elif line.startswith("state"):
                state = line[14:]
                if state == "Unpropagated":
                    activity.State = [glue2.computing_activity.ComputingActivity.STATE_STARTING]
                elif state == "Propagated":
                    activity.State = [glue2.computing_activity.ComputingActivity.STATE_STARTING]
                elif state == "Running":
                    activity.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
                elif state == "Corrupted":
                    activity.State = [glue2.computing_activity.ComputingActivity.STATE_FAILED]
                else:
                    self.error("unknown state: %s",state)
                    activity.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
                activity.State.append("nimbus:"+state)
            elif line.startswith("start time"):
                # this is really the time that Nimbus begins to start a job - it can take a while
                # use SubmissionTime to be compatible with ComputingActivityUpdateStep
                activity.SubmissionTime = _getAdminDateTime(line[14:])
                activity.ComputingManagerSubmissionTime = activity.SubmissionTime
            elif line.startswith("end time"):
                end_time = _getAdminDateTime(line[14:])
            elif line.startswith("memory"):
                activity.UsedMainMemory = int(line[14:])
            elif line.startswith("cpu count"):
                activity.RequestedSlots = int(line[14:])
            elif line.startswith("uri"):
                activity.Name = line[14:]
            else:
                pass
        activity.RequestedTotalWallTime = int(activity.RequestedSlots * \
                                              (time.mktime(end_time.timetuple()) - \
                                               time.mktime(activity.SubmissionTime.timetuple())))
        return activity

    def _fromCurrentReservations(self):
        activities = []

        file = open(os.path.join(self.nimbus_dir,"services","var","nimbus","current-reservations.txt"),"r")
        for line in file:
            activities.append(self._activityFromCurrentReservation(line))
        file.close()

        return activities

    def _activityFromCurrentReservation(self, line):
        activity = glue2.computing_activity.ComputingActivity()
        activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
        
        m = re.search("eprkey=(\d+)",line)
        activity.LocalIDFromManager = m.group(1)

        try:
            m = re.search("dn=\"([^\"]+)\"",line)
            activity.Owner = m.group(1)
            m = re.search("/O=Auto/OU=FutureGridNimbus/CN=(\S+)",activity.Owner)
            activity.LocalOwner = m.group(1)
        except AttributeError:
            m = re.search("uuid=\"([^\"]+)\"",line)
            activity.LocalOwner = m.group(1)

        try:
            m = re.search("creation=\"([^\"]+)\"",line)
            activity.StartTime = _getDateTime(m.group(1))
        except AttributeError:
            raise StepError("didn't find creation in: %s" % line)

        return activity

#######################################################################################################################

class ComputingActivityUpdateStep(glue2.computing_activity.ComputingActivityUpdateStep):
    def __init__(self):
        glue2.computing_activity.ComputingActivityUpdateStep.__init__(self)

        self._acceptParameter("nimbus_dir","the path to the NIMBUS directory",True)

        self.activities = {}

    def _run(self):
        self.info("running")
        step = ComputingActivitiesStep()    # use ComputingActivitiesStep to initialize cache of activities
        step.setParameters({},self.params)
        for activity in step._run():
            self.activities[activity.LocalIDFromManager] = activity

        try:
            nimbus_dir = self.params["nimbus_dir"]
        except KeyError:
            raise StepError("nimbus_dir parameter not specified")

        watcher = LogFileWatcher(self._logEntry, os.path.join(nimbus_dir,"var","services.log"))
        watcher.run()

    def _logEntry(self, log_file_name, line):
        if "defaults.ResourcepoolUtil" in line and "reserved" in line:
            # get VMM info in case it isn't in the create (e.g. cluster), but just create the cache entry
            self._activityFromReserve(line)
        elif "dbdefault.DBAccountingAdapter" in line and "create" in line:
            self._activityFromCreate(line)
        elif "manager.DelegatingManager" in line:
            if "SHUTDOWN-SAVE" in line or "TRASH" in line:
                self._activityFromShutdownTrash(line)
        elif "dbdefault.DBAccountingAdapter" in line and "destroy" in line:
            self._activityFromDestroy(line)
        elif "Start succeeded" in line:
            self._activityFromStartSucceeded(line)
        else:
            pass  # ignore

    def _activityFromReserve(self, line):
        activity = glue2.computing_activity.ComputingActivity()
        m = re.search("\[id-(\d+)\]",line)
        activity.LocalIDFromManager = m.group(1)
        try:
            m = re.search("resource pool entry '(\S+)'",line)
            activity.ExecutionNode = [m.group(1)]
        except AttributeError:
            logger.warn("expected to parse entry, but couldn't: %s",line)
            return
        self.activities[activity.LocalIDFromManager] = activity

    def _activityFromCreate(self, line):
        m = re.search("\[id-(\d+)\]",line)
        id = m.group(1)
        try:
            activity = self.activities[id]
        except KeyError:
            self.warning("didn't find activity %s in cache for create",id)
            activity = glue2.computing_activity.ComputingActivity()
            activity.LocalIDFromManager = id
            self.activities[activity.LocalIDFromManager] = activity
            try:
                m = re.search("vmm='(\S+)'",line)
                activity.ExecutionNode = [m.group(1)]
            except AttributeError:
                pass

        activity.State = glue2.computing_activity.ComputingActivity.STATE_STARTING
        activity.SubmissionTime = _getServicesLogDateTime(line[:23])
        activity.ComputingManagerSubmissionTime = activity.SubmissionTime

        try:
            m = re.search("ownerDN = '([^']+)'",line)
            activity.LocalOwner = m.group(1)
        except AttributeError:
            m = re.search("uuid = '([^\"]+)'",line)
            activity.LocalOwner = m.group(1)

        try:
            m = re.search("clientLaunchName='(\S+)'",line)
            activity.Name = m.group(1)
        except AttributeError:
            pass

        try:
            m = re.search("CPUCount = (\d+)",line)
            activity.RequestedSlots = int(m.group(1))
        except AttributeError:
            raise StepError("didn't find CPUCount in: %s" % line)

        try:
            m = re.search("minutesRequested = (\d+)",line)
            activity.RequestedTotalWallTime = int(m.group(1)) * 60 * activity.RequestedSlots
        except AttributeError:
            pass

        try:
            m = re.search("memory = (\d+)",line)
            activity.UsedMainMemory = int(m.group(1))
        except AttributeError:
            raise StepError("didn't find memory in: %s" % line)

        self.output(activity)

    def _activityFromStartSucceeded(self, line):
        m = re.search("\[id-(\d+)\]",line)
        id = m.group(1)
        try:
            activity = self.activities[id]
        except KeyError:
            self.warning("didn't find activity %s in cache for start succeeded",id)
            activity = glue2.computing_activity.ComputingActivity()
            activity.LocalIDFromManager = id
            self.activities[activity.LocalIDFromManager] = activity
        activity.State = glue2.computing_activity.ComputingActivity.STATE_RUNNING
        activity.StartTime = _getServicesLogDateTime(line[:23])
        self.output(activity)

    def _activityFromShutdownTrash(self, line):
        m = re.search("\[id-(\d+)\]",line)
        id = m.group(1)
        try:
            activity = self.activities[id]
        except KeyError:
            self.warning("didn't find activity %s in cache for destroy begins",id)
            activity = glue2.computing_activity.ComputingActivity()
            activity.LocalIDFromManager = id
            self.activities[activity.LocalIDFromManager] = activity
        activity.State = glue2.computing_activity.ComputingActivity.STATE_FINISHING
        activity.Extension["FinishingTime"] = _getServicesLogDateTime(line[:23])
        self.output(activity)
    
    def _activityFromDestroy(self, line):
        m = re.search("\[id-(\d+)\]",line)
        id = m.group(1)
        try:
            activity = self.activities[id]
            del self.activities[id]
        except KeyError:
            self.warning("didn't find activity %s in cache for destroy",id)
            activity = glue2.computing_activity.ComputingActivity()
            activity.LocalIDFromManager = id
            self.activities[activity.LocalIDFromManager] = activity
            try:
                m = re.search("ownerDN = '([^']+)'",line)
                activity.Owner = m.group(1)
                m = re.search("ownerDN = '.*CN=([^']+)'",line)
                activity.LocalOwner = m.group(1)
            except AttributeError:
                m = re.search("uuid = '([^\"]+)'",line)
                activity.LocalOwner = m.group(1)
            
        activity.State = glue2.computing_activity.ComputingActivity.STATE_FINISHED
        activity.EndTime = _getServicesLogDateTime(line[:23])
        activity.ComputingManagerEndTime = activity.EndTime

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

def _getDateTime(dtStr):
    # Example: Jun 17, 2012 2:45:07 AM
    d = datetime.datetime.strptime(dtStr,"%b %d, %Y %I:%M:%S %p")
    return datetime.datetime(d.year,d.month,d.day,d.hour,d.minute,d.second,d.microsecond,localtzoffset())

def _getAdminDateTime(dtStr):
    # Example: Mon Aug 13 10:59:12 CDT 2012
    d = datetime.datetime.strptime(dtStr,"%a %b %d %H:%M:%S %Z %Y")
    return datetime.datetime(d.year,d.month,d.day,d.hour,d.minute,d.second,d.microsecond,localtzoffset())

def _getServicesLogDateTime(dtStr):
    # Example: 2012-08-08 07:52:04,419
    d = datetime.datetime.strptime(dtStr,"%Y-%m-%d %H:%M:%S,%f")
    return datetime.datetime(d.year,d.month,d.day,d.hour,d.minute,d.second,d.microsecond,localtzoffset())

#######################################################################################################################
