
###############################################################################
#   Copyright 2013 The University of Texas at Austin                          #
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
import sys

import keystoneclient.v2_0.client
import novaclient.v1_1.client

from ipf.dt import *
from ipf.error import StepError

from glue2.log import LogFileWatcher
import glue2.computing_activity
import glue2.computing_endpoint
import glue2.computing_manager
import glue2.computing_service
import glue2.computing_share
import glue2.execution_environment

#######################################################################################################################

class Authentication():
    def __init__(self):
        self._acceptParameter("username","the OpenStack user (default is value in the OS_USERNAME env)",False)
        self._acceptParameter("password","the OpenStack password (default is value in the OS_PASSWORD env)",False)
        self._acceptParameter("tenant","the OpenStack tenant name (default is value in the OS_TENANT_NAME env)",False)
        self._acceptParameter("auth_url","the OpenStack authorization URL (default is value in the OS_AUTH_URL env)",
                              False)

    def _getAuthentication(step):
        try:
            username = step.params["username"]
        except KeyError:
            try:
                username = os.environ["OS_USERNAME"]
            except KeyError:
                raise StepError("username parameter not provided and OS_USERNAME not set in the environment")
        try:
            password = step.params["password"]
        except KeyError:
            try:
                password = os.environ["OS_PASSWORD"]
            except KeyError:
                raise StepError("password parameter not provided and OS_PASSWORD not set in the environment")
        try:
            tenant = step.params["tenant"]
        except KeyError:
            try:
                tenant = os.environ["OS_TENANT_NAME"]
            except KeyError:
                raise StepError("tenant parameter not provided and OS_TENANT_NAME not set in the environment")
        try:
            auth_url = step.params["auth_url"]
        except KeyError:
            try:
                auth_url = os.environ["OS_AUTH_URL"]
            except KeyError:
                raise StepError("auth_url parameter not provided and OS_AUTH_URL not set in the environment")
        return (username,password,tenant,auth_url)

#######################################################################################################################

class ComputingServiceStep(glue2.computing_service.ComputingServiceStep):
    def __init__(self):
        glue2.computing_service.ComputingServiceStep.__init__(self)

    def _run(self):
        service = glue2.computing_service.ComputingService()
        service.Name = "OpenStack"
        service.Capability = ["executionmanagement.jobexecution",
                              "executionmanagement.jobdescription",
                              "executionmanagement.jobmanager"
                              ]
        service.Type = "org.openstack"
        service.QualityLevel = "production"

        return service

#######################################################################################################################

class ComputingManagerStep(glue2.computing_manager.ComputingManagerStep):
    def __init__(self):
        glue2.computing_manager.ComputingManagerStep.__init__(self)

        self._acceptParameter("openstack_version","the OpenStack version",False)

    def _run(self):
        manager = glue2.computing_manager.ComputingManager()
        manager.ProductName = "OpenStack"
        manager.Name = "OpenStack"
        manager.Reservation = False
        manager.BulkSubmission = True

        try:
            manager.Version = self.params["openstack_version"]
        except KeyError:
            pass

        return manager

#######################################################################################################################

class ComputingEndpointStep(glue2.computing_endpoint.ComputingEndpointStep, Authentication):
    def __init__(self):
        glue2.computing_endpoint.ComputingEndpointStep.__init__(self)
        Authentication.__init__(self)

        self.description = "create ComputingEndpoints for OpenStack"
        self._acceptParameter("openstack_version","the OpenStack version",False)

    def _run(self):
        (username,password,tenant,auth_url) = self._getAuthentication()
        keystone = keystoneclient.v2_0.client.Client(username=username,
                                                     password=password,
                                                     tenant_name=tenant,
                                                     auth_url=auth_url)
        endpoints = []
        kendpoints = {}
        for endpoint in keystone.endpoints.list():
            kendpoints[endpoint.service_id] = endpoint
        for service in keystone.services.list():
            if service.name == "nova":
                endpoint = self._getEndpoint()
                endpoint.Name = "openstack-nova"
                endpoint.URL = kendpoints[service.id].publicurl
                endpoint.Technology = "REST"
                endpoint.InterfaceName = "Nova"
                endpoints.append(endpoint)
            if service.name == "ec2":
                endpoint = self._getEndpoint()
                endpoint.Name = "openstack-ec2"
                endpoint.URL = kendpoints[service.id].publicurl
                endpoint.Technology = "REST"
                endpoint.InterfaceName = "EC2"
                endpoints.append(endpoint)

        return endpoints

    def _getEndpoint(self):
        endpoint = glue2.computing_endpoint.ComputingEndpoint()
        endpoint.Capability = ["executionmanagement.jobdescription",
                               "executionmanagement.jobexecution",
                               "executionmanagement.jobmanager",
                               ]
        endpoint.Implementor = "OpenStack"
        endpoint.ImplementationName = "OpenStack"
        try:
            endpoint.ImplementationVersion = self.params["openstack_version"]
        except KeyError:
            pass
        endpoint.QualityLevel = "production"

        return endpoint

#######################################################################################################################

class ComputingActivitiesStep(glue2.computing_activity.ComputingActivitiesStep, Authentication):
    def __init__(self):
        glue2.computing_activity.ComputingActivitiesStep.__init__(self)
        Authentication.__init__(self)

        self.users = {}
        self.flavors = {}

    def _getUser(self, keystone, id):
        if id not in self.users:
            self.users[id] = keystone.users.get(id)
        return self.users[id]

    def _getFlavor(self, nova, id):
        if id not in self.users:
            self.flavors[id] = nova.flavors.get(id)
        return self.flavors[id]

    def _run(self):
        (username,password,tenant,auth_url) = self._getAuthentication()
        nova = novaclient.v1_1.client.Client(username,password,tenant,auth_url,no_cache=True)
        keystone = keystoneclient.v2_0.client.Client(username=username,
                                                     password=password,
                                                     tenant_name=tenant,
                                                     auth_url=auth_url)

        activities = []
        for server in nova.servers.list(search_opts={"all_tenants": 1}):
            activities.append(self._fromService(server,nova,keystone))
        return activities

    def _fromService(self, server, nova, keystone):
        activity = glue2.computing_activity.ComputingActivity()
        activity.LocalIDFromManager = server.id
        activity.Name = server.name
        activity.LocalOwner = self._getUser(keystone,server.user_id).name
        #activity.Extension["UserId"] = server.user_id

        if server.status == "BUILD":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_STARTING]
        elif server.status == "ACTIVE":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
        elif server.status == "PAUSED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_SUSPENDED]
        elif server.status == "SUSPENDED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_SUSPENDED]
        elif server.status == "STOPPED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_SUSPENDED]
        elif server.status == "SHUTOFF":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_SUSPENDED]
        elif server.status == "RESCUED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
        elif server.status == "RESIZED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_RUNNING]
        elif server.status == "SOFT_DELETED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
        elif server.status == "DELETED":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_TERMINATED]
        elif server.status == "ERROR":
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_FAILED]
        else:
            activity.State = [glue2.computing_activity.ComputingActivity.STATE_UNKNOWN]
            self.warning("couldn't handle server status '%s'" % server.status)
        activity.State.append("openstack:"+server.status)

        activity.SubmissionTime = _getDateTime(server.created)
        activity.ComputingManagerSubmissionTime = activity.SubmissionTime

        flavor = self._getFlavor(nova,server.flavor["id"])
        activity.RequestedSlots = flavor.vcpus
        activity.UsedMainMemory = flavor.ram

        addresses = []
        for adds in server.addresses.values():
            for add in adds:
                addresses.append(add["addr"])
        activity.Extension["IpAddresses"] = addresses

        image = nova.images.get(server.image["id"])
        activity.RequestedApplicationEnvironment = [image.name]

        activity.ExecutionNode = [getattr(server,"OS-EXT-SRV-ATTR:host")]

        return activity

#######################################################################################################################

class ComputingActivityUpdateStep(glue2.computing_activity.ComputingActivityUpdateStep):
    def __init__(self):
        glue2.computing_activity.ComputingActivityUpdateStep.__init__(self)

    def _run(self):
        # The nova logging doesn't seem good enough to support this activity.
        # An alternative is to query the nova database in MySQL.
        raise NotImplementedError()


#######################################################################################################################

class ComputingSharesStep(glue2.computing_share.ComputingSharesStep):
    def __init__(self):
        glue2.computing_share.ComputingSharesStep.__init__(self)

    def _run(self):
        return []

#######################################################################################################################

class ExecutionEnvironmentsStep(glue2.execution_environment.ExecutionEnvironmentsStep, Authentication):
    def __init__(self):
        glue2.execution_environment.ExecutionEnvironmentsStep.__init__(self)
        Authentication.__init__(self)

    def _run(self):
        (username,password,tenant,auth_url) = self._getAuthentication()
        nova = novaclient.v1_1.client.Client(username,password,tenant,auth_url,no_cache=True)
        keystone = keystoneclient.v2_0.client.Client(username=username,
                                                     password=password,
                                                     tenant_name=tenant,
                                                     auth_url=auth_url)

        exec_envs = []
        host_names = set()
        for host in nova.hosts.list_all():
            host_names.add(host.host_name)
        for host_name in host_names:
            exec_env = self._getExecEnv(nova,host_name)
            if exec_env is not None:
                exec_envs.append(exec_env)
        return exec_envs

    def _getExecEnv(self, nova, host_name):
        node = glue2.execution_environment.ExecutionEnvironment()
        node.Name = host_name
        node.TotalInstances = 1
        node.UnavailableInstances = 0

        try:
            entries = nova.hosts.get(host_name)
        except novaclient.exceptions.NotFound, e:
            return None   # this is ok - non-compute hosts don't have any info
        for entry in entries:
            if entry.project == "(total)":
                node.LogicalCPUs = entry.cpu
                node.MainMemorySize = entry.memory_mb
                node.Extension["DiskSize"] = entry.disk_gb
            if entry.project == "(used_now)":
                if entry.cpu > 0:
                    node.UsedInstances = 1
                else:
                    node.UsedInstances = 0
        return node

#######################################################################################################################

def _getDateTime(dtStr):
    # Example: 2013-10-27T09:55:02Z
    d = datetime.datetime.strptime(dtStr,"%Y-%m-%dT%H:%M:%SZ")
    return datetime.datetime(d.year,d.month,d.day,d.hour,d.minute,d.second,d.microsecond,tzoffset(0))

#######################################################################################################################
