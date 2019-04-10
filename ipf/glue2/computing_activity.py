
###############################################################################
#   Copyright 2011-2014 The University of Texas at Austin                     #
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

import json
import os
import time
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.paths import IPF_VAR_PATH
from ipf.sysinfo import ResourceName

from activity import *
from step import GlueStep

#######################################################################################################################

class ComputingActivitiesStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "produces a document containing one or more GLUE 2 ComputingActivity"
        self.time_out = 30
        self.requires = [ResourceName]
        self.produces = [ComputingActivities]
        self._acceptParameter("hide_job_attribs",
                              "a list of ComputingActivity attributes to hide (optional)",
                              False)
        self._acceptParameter("queues",
                              "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. the expression is processed in order and the value for a queue at the end determines if it is shown.",
                              False)

        self.resource_name = None
        
    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name

        activities = self._run()
        for activity in activities:
            if activity.LocalOwner is None:
                activity.id = "%s.unknown.%s" % (activity.LocalIDFromManager,self.resource_name)
            else:
                activity.id = "%s.%s.%s" % (activity.LocalIDFromManager,activity.LocalOwner,self.resource_name)
            activity.ID = "urn:glue2:ComputingActivity:%s.%s" % (activity.LocalIDFromManager,self.resource_name)
            if activity.Queue is not None:
                activity.ShareID = "urn:glue2:ComputingShare:%s.%s" % (activity.Queue,self.resource_name)
            activity.hide = self.params.get("hide_job_attribs",[])

        self._output(ComputingActivities(self.resource_name,activities))

    def _run(self):
        raise StepError("ComputingActivitiesStep._run not overriden")

    def _jobStateKey(self, job):
        # assumes the IPF state is the first one
        if job.State[0] == ComputingActivity.STATE_RUNNING:
            return 1
        if job.State[0] == ComputingActivity.STATE_STARTING:
            return 2
        if job.State[0] == ComputingActivity.STATE_SUSPENDED:
            return 3
        if job.State[0] == ComputingActivity.STATE_PENDING:
            return 4
        if job.State[0] == ComputingActivity.STATE_HELD:
            return 5
        if job.State[0] == ComputingActivity.STATE_FINISHING:
            return 6
        if job.State[0] == ComputingActivity.STATE_TERMINATING:
            return 7
        if job.State[0] == ComputingActivity.STATE_FINISHED:
            return 8
        if job.State[0] == ComputingActivity.STATE_TERMINATED:
            return 9
        if job.State[0] == ComputingActivity.STATE_FAILED:
            return 10
        if job.State[0] == ComputingActivity.STATE_UNKNOWN:
            return 11
        return 12  # above should be all of them, but...

#######################################################################################################################

class ComputingActivityUpdateStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "produces a document containing an update to a GLUE 2 ComputingActivity"
        self.time_out = None
        self.requires = [ResourceName]
        self.produces = [ComputingActivity]

        self._acceptParameter("position_file","the file to store the read position into the log file - relative to IPF_VAR_PATH (default none)",False)

        self._acceptParameter("hide_job_attribs",
                              "a comma-separated list of ComputingActivity attributes to hide (optional)",
                              False)
        self._acceptParameter("queues",
                              "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. the expression is processed in order and the value for a queue at the end determines if it is shown.",
                              False)


        self.resource_name = None
        
    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name

        try:
            self.position_file = os.path.join(IPF_VAR_PATH,self.params["position_file"])
        except KeyError:
            self.position_file = None
        
        self._run()

    def output(self, activity):
        if activity.LocalOwner is None:
            activity.id = "%s.unknown.%s" % (activity.LocalIDFromManager,self.resource_name)
        else:
            activity.id = "%s.%s.%s" % (activity.LocalIDFromManager,activity.LocalOwner,self.resource_name)
        activity.ID = "urn:glue2:ComputingActivity:%s.%s" % (activity.LocalIDFromManager,self.resource_name)
        if activity.Queue is not None:
            activity.ShareID = "urn:glue2:ComputingShare:%s.%s" % (activity.Queue,self.resource_name)
        activity.hide = self.params.get("hide_job_attribs",[])
        
        self._output(activity)

    def _run(self):
        raise StepError("ComputingActivityUpdateStep._run not overriden")

#######################################################################################################################

class ComputingActivity(Activity):

    STATE_PENDING = "ipf:pending"
    STATE_HELD = "ipf:held"
    STATE_STARTING = "ipf:starting"
    STATE_RUNNING = "ipf:running"
    STATE_SUSPENDED = "ipf:suspended"
    STATE_TERMINATING = "ipf:terminating"
    STATE_TERMINATED = "ipf:terminated"
    STATE_FINISHING = "ipf:finishing"
    STATE_FINISHED = "ipf:finished"
    STATE_FAILED = "ipf:failed"
    STATE_UNKNOWN = "ipf:unknown"

    def __init__(self):
        Activity.__init__(self)

        self.hide = set()    # attributes that shouldn't be published

        self.Type = None                           # string (restricted)
        self.IDFromEndpoint = None                 # uri
        self.LocalIDFromManager = None             # string
        self.JobDescription = None                 # string (restricted)
        self.State = []                            # list of strings (restricted) - first should be IPF state
        self.RestartState = []                     # list of strings (restricted)
        self.ExitCode = None                       # integer
        self.ComputingManagerExitCode = None       # string
        self.Error = []                            # list of string
        self.WaitingPosition = None                # integer
        self.Owner = "unknown"                     # string
        self.LocalOwner = None                     # string
        self.RequestedTotalWallTime = None         # integer (seconds) - wall time * slots
        self.RequestedTotalCPUTime = None          # integer (seconds) - cpu time * slots
        self.RequestedSlots = None                 # integer
        self.RequestedAcceleratorSlots = None                 # integer
        self.RequestedApplicationEnvironment = []  # list of strings
        self.StdIn = None                          # string
        self.StdOut = None                         # string
        self.StdErr = None                         # string
        self.LogDir = None                         # string
        self.ExecutionNode = []                    # list of strings
        self.Queue = None                          # string
        self.UsedTotalWallTime = None              # integer (s)
        self.UsedTotalCPUTime = None               # integer (s)
        self.UsedMainMemory = None                 # integer (MB)
        self.SubmissionTime = None                 # datetime
        self.ComputingManagerSubmissionTime = None # datetime
        self.StartTime = None                      # datetime
        self.ComputingManagerEndTime = None        # datetime
        self.EndTime = None                        # datetime
        self.WorkingAreaEraseTime = None           # datetime
        self.ProxyExpirationTime = None            # datetime
        self.SubmissionHost = None                 # string
        self.SubmissionClientName = None           # string
        self.OtherMessages = []                    # list of string
        # use Endpoint, Share, Resource instead of ComputingEndpoint, ComputingShare, ExecutionEnvironment

    def __str__(self):
        return json.dumps(ComputingActivityOgfJson(self).toJson(),sort_keys=True,indent=4)

#######################################################################################################################

class ComputingActivityTeraGridXml(ActivityTeraGridXml):
    data_cls = ComputingActivity

    def __init__(self, data):
        ActivityTeraGridXml.__init__(self,data)

    def get(self):
        return self.toDom().toxml()

    def toDom(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingActivity")
        doc.documentElement.appendChild(root)
        self.addToDomElement(doc,root)

        return doc

    def addToDomElement(self, doc, element):
        ActivityTeraGridXml.addToDomElement(self,doc,element)

        hide = self.data.hide

        if self.data.Type is not None and "Type" not in hide:
            e = doc.createElement("Type")
            e.appendChild(doc.createTextNode(self.data.Type))
            element.appendChild(e)
        if self.data.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            e = doc.createElement("IDFromEndpoint")
            e.appendChild(doc.createTextNode(self.data.IDFromEndpoint))
            element.appendChild(e)
        if self.data.LocalIDFromManager is not None and "LocalIDFromManager" not in hide:
            e = doc.createElement("LocalIDFromManager")
            e.appendChild(doc.createTextNode(self.data.LocalIDFromManager))
            element.appendChild(e)
        if self.data.JobDescription is not None and "JobDescription" not in hide:
            e = doc.createElement("JobDescription")
            e.appendChild(doc.createTextNode(self.data.JobDescription))
            element.appendChild(e)
        if len(self.data.State) > 0:
            e = doc.createElement("State")
            e.appendChild(doc.createTextNode(self.data.State[0]))  # just the ipf:... state
            element.appendChild(e)
        if len(self.data.RestartState) > 0 and "RestartState" not in hide:
            e = doc.createElement("RestartState")
            e.appendChild(doc.createTextNode(self.data.RestartState[0]))
            element.appendChild(e)
        if self.data.ExitCode is not None and "ExitCode" not in hide:
            e = doc.createElement("ExitCode")
            e.appendChild(doc.createTextNode(str(self.data.ExitCode)))
            element.appendChild(e)
        if self.data.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            e = doc.createElement("ComputingManagerExitCode")
            e.appendChild(doc.createTextNode(str(self.data.ComputingManagerExitCode)))
            element.appendChild(e)
        if "Error" not in hide:
            for error in self.data.Error:
                e = doc.createElement("Error")
                e.appendChild(doc.createTextNode(error))
                element.appendChild(e)
        if self.data.WaitingPosition is not None and "WaitingPosition" not in hide:
            e = doc.createElement("WaitingPosition")
            e.appendChild(doc.createTextNode(str(self.data.WaitingPosition)))
            element.appendChild(e)
        if self.data.Owner is not None and "Owner" not in hide:
            e = doc.createElement("Owner")
            e.appendChild(doc.createTextNode(self.data.Owner))
            element.appendChild(e)
        if self.data.LocalOwner is not None and "LocalOwner" not in hide:
            e = doc.createElement("LocalOwner")
            e.appendChild(doc.createTextNode(self.data.LocalOwner))
            element.appendChild(e)
        if self.data.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            e = doc.createElement("RequestedTotalWallTime")
            e.appendChild(doc.createTextNode(str(self.data.RequestedTotalWallTime)))
            element.appendChild(e)
        if self.data.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            e = doc.createElement("RequestedTotalCPUTime")
            e.appendChild(doc.createTextNode(str(self.data.RequestedTotalCPUTime)))
            element.appendChild(e)
        if self.data.RequestedSlots is not None and "RequestedSlots" not in hide:
            e = doc.createElement("RequestedSlots")
            e.appendChild(doc.createTextNode(str(self.data.RequestedSlots)))
            element.appendChild(e)
        if "RequestedApplicationEnvironment" not in hide:
            for appEnv in self.data.RequestedApplicationEnvironment:
                e = doc.createElement("RequestedApplicationEnvironment")
                e.appendChild(doc.createTextNode(appEnv))
                element.appendChild(e)
        if self.data.StdIn is not None and "StdIn" not in hide:
            e = doc.createElement("StdIn")
            e.appendChild(doc.createTextNode(self.data.StdIn))
            element.appendChild(e)
        if self.data.StdOut is not None and "StdOut" not in hide:
            e = doc.createElement("StdOut")
            e.appendChild(doc.createTextNode(self.data.StdOut))
            element.appendChild(e)
        if self.data.StdErr is not None and "StdErr" not in hide:
            e = doc.createElement("StdErr")
            e.appendChild(doc.createTextNode(self.data.StdErr))
            element.appendChild(e)
        if self.data.LogDir is not None and "LogDir" not in hide:
            e = doc.createElement("LogDir")
            e.appendChild(doc.createTextNode(self.data.LogDir))
            element.appendChild(e)
        if "ExecutionNode" not in hide:
            for node in self.data.ExecutionNode:
                e = doc.createElement("ExecutionNode")
                e.appendChild(doc.createTextNode(node))
                element.appendChild(e)
        if self.data.Queue is not None and "Queue" not in hide:
            e = doc.createElement("Queue")
            e.appendChild(doc.createTextNode(self.data.Queue))
            element.appendChild(e)
        if self.data.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            e = doc.createElement("UsedTotalWallTime")
            e.appendChild(doc.createTextNode(str(self.data.UsedTotalWallTime)))
            element.appendChild(e)
        if self.data.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            e = doc.createElement("UsedTotalCPUTime")
            e.appendChild(doc.createTextNode(str(self.data.UsedTotalCPUTime)))
            element.appendChild(e)
        if self.data.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            e = doc.createElement("UsedMainMemory")
            e.appendChild(doc.createTextNode(str(self.data.UsedMainMemory)))
            element.appendChild(e)
        if self.data.SubmissionTime is not None and "SubmissionTime" not in hide:
            e = doc.createElement("SubmissionTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.SubmissionTime)))
            element.appendChild(e)
        if self.data.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            e = doc.createElement("ComputingManagerSubmissionTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.ComputingManagerSubmissionTime)))
            element.appendChild(e)
        if self.data.StartTime is not None and "StartTime" not in hide:
            e = doc.createElement("StartTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.StartTime)))
            element.appendChild(e)
        if self.data.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            e = doc.createElement("ComputingManagerEndTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.ComputingManagerEndTime)))
            element.appendChild(e)
        if self.data.EndTime is not None and "EndTime" not in hide:
            e = doc.createElement("EndTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.EndTime)))
            element.appendChild(e)
        if self.data.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            e = doc.createElement("WorkingAreaEraseTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.WorkingAreaEraseTime)))
            element.appendChild(e)
        if self.data.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            e = doc.createElement("ProxyExpirationTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.data.ProxyExpirationTime)))
            element.appendChild(e)
        if self.data.SubmissionHost is not None and "SubmissionHost" not in hide:
            e = doc.createElement("SubmissionHost")
            e.appendChild(doc.createTextNode(self.data.SubmissionHost))
            element.appendChild(e)
        if self.data.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            e = doc.createElement("SubmissionClientName")
            e.appendChild(doc.createTextNode(self.data.SubmissionClientName))
            element.appendChild(e)
        for message in self.data.OtherMessages:
            e = doc.createElement("OtherMessages")
            e.appendChild(doc.createTextNode(message))
            element.appendChild(e)
        if self.data.EndpointID is not None:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(self.data.EndpointID))
            element.appendChild(e)
        if self.data.ShareID is not None:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(self.data.ShareID))
            element.appendChild(e)
        if self.data.ResourceID is not None:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(self.data.ResourceID))
            element.appendChild(e)

        return doc

#######################################################################################################################

class ComputingActivityOgfJson(ActivityOgfJson):
    data_cls = ComputingActivity

    def __init__(self, data):
        ActivityOgfJson.__init__(self,data)

    def get(self):
        return json.dumps(self.toJson(),sort_keys=True,indent=4)

    def toJson(self):
        hide = self.data.hide
        
        doc = ActivityOgfJson.toJson(self)

        if self.data.Type is not None and "Type" not in hide:
            doc["Type"] = self.data.Type
        if self.data.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            doc["ActivityFromEndpoint"] = self.data.IDFromEndpoint
        if self.data.LocalIDFromManager is not None and "LocalIDFromManaer" not in hide:
            doc["LocalIDFromManager"] = self.data.LocalIDFromManager
        if self.data.JobDescription is not None and "JobDescription" not in hide:
            doc["JobDescription"] = self.data.JobDescription
        if len(self.data.State) > 0:
            doc["State"] = self.data.State
        else:
            doc["State"] = [ComputingActivity.STATE_UNKNOWN,]
        if len(self.data.RestartState) > 0 and "RestartState" not in hide:
            doc["RestartState"] = self.data.RestartState
        if self.data.ExitCode is not None and "ExitCode" not in hide:
            doc["ExitCode"] = self.data.ExitCode
        if self.data.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            doc["ComputingManagerExitCode"] = self.data.ComputingManagerExitCode
        if len(self.data.Error) > 0 and "Error" not in hide:
            doc["Error"] = self.data.Error
        if self.data.WaitingPosition is not None and "WaitingPosition" not in hide:
            doc["WaitingPosition"] = self.data.WaitingPosition
        doc["Owner"] = self.data.Owner
        if self.data.LocalOwner is not None and "LocalOwner" not in hide:
            doc["LocalOwner"] = self.data.LocalOwner
        if self.data.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            doc["RequestedTotalWallTime"] = self.data.RequestedTotalWallTime
        if self.data.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            doc["RequestedTotalCPUTime"] = self.data.RequestedTotalCPUTime
        if self.data.RequestedSlots is not None and "RequestedSlots" not in hide:
            doc["RequestedSlots"] = self.data.RequestedSlots
        if len(self.data.RequestedApplicationEnvironment) > 0 and "RequestedApplicationEnvironment" not in hide:
            doc["RequestedApplicationEnvironment"] = self.data.RequestedApplicationEnvironment
        if self.data.StdIn is not None and "StdIn" not in hide:
            doc["StdIn"] = self.data.StdIn
        if self.data.StdOut is not None and "StdOut" not in hide:
            doc["StdOut"] = self.data.StdOut
        if self.data.StdErr is not None and "StdErr" not in hide:
            doc["StdErr"] = self.data.StdErr
        if self.data.LogDir is not None and "LogDir" not in hide:
            doc["LogDir"] = self.data.LogDir
        if len(self.data.ExecutionNode) > 0 and "ExecutionNode" not in hide:
            doc["ExecutionNode"] = self.data.ExecutionNode
        if self.data.Queue is not None and "Queue" not in hide:
            doc["Queue"] = self.data.Queue
        if self.data.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            doc["UsedTotalWallTime"] = self.data.UsedTotalWallTime
        if self.data.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            doc["UsedTotalCPUTime"] = self.data.UsedTotalCPUTime
        if self.data.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            doc["UsedMainMemory"] = self.data.UsedMainMemory
        if self.data.SubmissionTime is not None and "SubmissionTime" not in hide:
            doc["SubmissionTime"] = dateTimeToText(self.data.SubmissionTime)
        if self.data.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            doc["ComputingManagerSubmissionTime"] = dateTimeToText(self.data.ComputingManagerSubmissionTime)
        if self.data.StartTime is not None and "StartTime" not in hide:
            doc["StartTime"] = dateTimeToText(self.data.StartTime)
        if self.data.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            doc["ComputingManagerEndTime"] = dateTimeToText(self.data.ComputingManagerEndTime)
        if self.data.EndTime is not None and "EndTime" not in hide:
            doc["EndTime"] = dateTimeToText(self.data.EndTime)
        if self.data.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            doc["WorkingAreaEraseTime"] = dateTimeToText(self.data.WorkingAreaEraseTime)
        if self.data.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            doc["ProxyExpirationTime"] = dateTimeToText(self.data.ProxyExpirationTime)
        if self.data.SubmissionHost is not None and "SubmissionHost" not in hide:
            doc["SubmissionHost"] = self.data.SubmissionHost
        if self.data.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            doc["SubmissionClientName"] = self.data.SubmissionClientName
        if len(self.data.OtherMessages) > 0 and "OtherMessages" not in hide:
            doc["OtherMessages"] = self.data.OtherMessages

        return doc

#######################################################################################################################
    
class ComputingActivities(Data):
    def __init__(self, id, activities):
        Data.__init__(self,id)
        self.activities = activities
    
#######################################################################################################################

class ComputingActivitiesTeraGridXml(Representation):
    data_cls = ComputingActivities

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for activity in self.data.activities:
            adoc = ComputingActivityTeraGridXml.toDom(activity)
            doc.documentElement.appendChild(adoc.documentElement.firstChild)
        return doc.toxml()
        #return doc.toprettyxml()

#######################################################################################################################

class ComputingActivitiesOgfJson(Representation):
    data_cls = ComputingActivities

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        adoc = []
        for activity in self.data.activities:
            adoc.append(ComputingActivityOgfJson(activity).toJson())
        return json.dumps(adoc,sort_keys=True,indent=4)
    
#######################################################################################################################
