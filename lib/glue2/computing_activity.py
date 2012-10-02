
###############################################################################
#   Copyright 2011-2012 The University of Texas at Austin                     #
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

import json    # new in Python 2.6
import time
from xml.dom.minidom import getDOMImplementation

from ipf.data import Data, Representation
from ipf.dt import *
from ipf.error import StepError
from ipf.name import ResourceName

from glue2.step import GlueStep

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
                activity.ComputingShare = "urn:glue2:ComputingShare:%s.%s" % (activity.Queue,self.resource_name)
            activity.hide = self.params.get("hide_job_attribs",[])

        self._output(ComputingActivities(self.resource_name,activities))

    def _run(self):
        raise StepError("ComputingActivitiesStep._run not overriden")

#######################################################################################################################

class ComputingActivityUpdateStep(GlueStep):
    def __init__(self):
        GlueStep.__init__(self)

        self.description = "produces a document containing an update to a GLUE 2 ComputingActivity"
        self.time_out = None
        self.requires = [ResourceName]
        self.produces = [ComputingActivity]
        self._acceptParameter("hide_job_attribs",
                              "a comma-separated list of ComputingActivity attributes to hide (optional)",
                              False)
        self._acceptParameter("queues",
                              "An expression describing the queues to include (optional). The syntax is a series of +<queue> and -<queue> where <queue> is either a queue name or a '*'. '+' means include '-' means exclude. the expression is processed in order and the value for a queue at the end determines if it is shown.",
                              False)

        self.resource_name = None
        
    def run(self):
        self.resource_name = self._getInput(ResourceName).resource_name
        
        self._run()

    def output(self, activity):
        if activity.LocalOwner is None:
            activity.id = "%s.unknown.%s" % (activity.LocalIDFromManager,self.resource_name)
        else:
            activity.id = "%s.%s.%s" % (activity.LocalIDFromManager,activity.LocalOwner,self.resource_name)
        activity.ID = "urn:glue2:ComputingActivity:%s.%s" % (activity.LocalIDFromManager,self.resource_name)
        if activity.Queue is not None:
            activity.ComputingShare = "urn:glue2:ComputingShare:%s.%s" % (activity.Queue,self.resource_name)
        activity.hide = self.params.get("hide_job_attribs",[])
        
        self._output(activity)

    def _run(self):
        raise StepError("ComputingActivityUpdateStep._run not overriden")

#######################################################################################################################

class ComputingActivity(Data):

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
        Data.__init__(self)

        self.hide = set()    # attributes that shouldn't be published

        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = None
        self.ID = None      # string (uri)
        self.Name = None    # string
        self.OtherInfo = [] # list of string
        self.Extension = {} # (key,value) strings

        # Activity
        self.UserDomain = None # string uri
        self.Endpoint = None   # string uri
        self.Share = None      # string uri
        self.Resource = None   # string uri
        self.Activity = []     # list of string uri

        # ComputingActivity
        self.Type = None                           # string (restricted)
        self.IDFromEndpoint = None                 # uri
        self.LocalIDFromManager = None             # string
        self.JobDescription = None                 # string (restricted)
        self.State = None                          # string (restricted)
        self.RestartState = None                   # string (restricted)
        self.ExitCode = None                       # integer
        self.ComputingManagerExitCode = None       # string
        self.Error = []                            # list of string
        self.WaitingPosition = None                # integer
        self.Owner = "unknown"                     # string
        self.LocalOwner = None                     # string
        self.RequestedTotalWallTime = None         # integer (seconds) - wall time * slots
        self.RequestedTotalCPUTime = None          # integer (seconds) - cpu time * slots
        self.RequestedSlots = None                 # integer
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
        self.ComputingEndpoint = None              # uri
        self.ComputingShare = None                 # string (LocalID)
        self.ExecutionEnvironment = None           # uri

    def __str__(self):
        return json.dumps(ComputingActivityIpfJson.toJson(self),sort_keys=True,indent=4)

    ###################################################################################################################

    # legacy
    def fromJson(self, doc):
        # Entity
        if "CreationTime" in doc:
            self.CreationTime = textToDateTime(doc["CreationTime"])
        else:
            self.CreationTime = None
        self.Validity = doc.get("Validity")
        self.ID = doc.get("ID")
        self.Name = doc.get("Name")
        self.OtherInfo = doc.get("OtherInfo",[])
        self.Extension = doc.get("Extension",{})
        for name in doc.get("Extension",{}):
            if "Time" in name:
                try:
                    self.Extension[name] = textToDateTime(doc["Extension"][name])
                except:
                    self.Extension[name] = doc["Extension"][name]
            else:
                self.Extension[name] = doc["Extension"][name]

        # Activity
        self.UserDomain = doc.get("UserDomain")
        self.Endpoint = doc.get("Endpoint")
        self.Share = doc.get("Share")
        self.Resource = doc.get("Resource")
        self.Activity = doc.get("Activity",[])

        # ComputingActivity
        self.Type = doc.get("Type")
        self.IDFromEndpoint = doc.get("IDFromEndpoint")
        self.LocalIDFromManager = doc.get("LocalIDFromManager")
        self.JobDescription = doc.get("JobDescription")
        self.State = doc.get("State")
        self.RestartState = doc.get("RestartState")
        self.ExitCode = doc.get("ExitCode")
        self.ComputingManagerExitCode = doc.get("ComputingManagerExitCode")
        self.Error = doc.get("Error",[])
        self.WaitingPosition = doc.get("WaitingPosition")
        self.Owner = doc.get("Owner","unknown")
        self.LocalOwner = doc.get("LocalOwner")
        self.RequestedTotalWallTime = doc.get("RequestedTotalWallTime")
        self.RequestedTotalCPUTime = doc.get("RequestedTotalCPUTime")
        self.RequestedSlots = doc.get("RequestedSlots")
        self.RequestedApplicationEnvironment = doc.get("RequestedApplicationEnvironment",[])
        self.StdIn = doc.get("StdIn")
        self.StdOut = doc.get("StdOut")
        self.StdErr = doc.get("StdErr")
        self.LogDir = doc.get("LogDir")
        self.ExecutionNode = doc.get("ExecutionNode",[])
        self.Queue = doc.get("Queue")
        self.UsedTotalWallTime = doc.get("UsedTotalWallTime")
        self.UsedTotalCPUTime = doc.get("UsedTotalCPUTime")
        self.UsedMainMemory = doc.get("UsedMainMemory")
        self.SubmissionTime = textToDateTime(doc.get("SubmissionTime"))
        self.ComputingManagerSubmissionTime = textToDateTime(doc.get("ComputingManagerSubmissionTime"))
        self.StartTime = textToDateTime(doc.get("StartTime"))
        self.ComputingManagerEndTime = textToDateTime(doc.get("ComputingManagerEndTime"))
        self.EndTime = textToDateTime(doc.get("EndTime"))
        self.WorkingAreaEraseTime = textToDateTime(doc.get("WorkingAreaEraseTime"))
        self.ProxyExpirationTime = textToDateTime(doc.get("ProxyExpirationTime"))
        self.SubmissionHost = doc.get("SubmissionHost")
        self.SubmissionClientName = doc.get("SubmissionClientName")
        self.OtherMessages = doc.get("OtherMessages",[])
        self.ComputingEndpoint = doc.get("ComputingEndpoint",[])
        self.ComputingShare = doc.get("ComputingShare",[])
        self.ExecutionEnvironment = doc.get("ExecutionEnvironment",[])

#######################################################################################################################

class ComputingActivityTeraGridXml(Representation):
    data_cls = ComputingActivity

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_TEXT_XML,data)

    def get(self):
        return self.toDom(self.data).toxml()

    @staticmethod
    def toDom(activity):
        hide = activity.hide
        
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingActivity")
        doc.documentElement.appendChild(root)

        # Entity
        e = doc.createElement("CreationTime")
        e.appendChild(doc.createTextNode(dateTimeToText(activity.CreationTime)))
        if activity.Validity is not None:
            e.setAttribute("Validity",str(activity.Validity))
        root.appendChild(e)

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(activity.ID))
        root.appendChild(e)

        if activity.Name is not None and "Name" not in hide:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(activity.Name))
            root.appendChild(e)
        for info in activity.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        if "Extension" not in hide:
            for key in activity.Extension.keys():
                e = doc.createElement("Extension")
                e.setAttribute("Key",key)
                e.appendChild(doc.createTextNode(activity.Extension[key]))
                root.appendChild(e)

        # Activity
        if activity.UserDomain is not None and "UserDomain" not in hide:
            e = doc.createElement("UserDomain")
            e.appendChild(doc.createTextNode(activity.UserDomain))
            root.appendChild(e)
        if activity.Endpoint is not None and "Endpoint" not in hide:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(activity.Endpoint))
            root.appendChild(e)
        if activity.Share is not None and "Share" not in hide:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(activity.Share))
            root.appendChild(e)
        if activity.Resource is not None and "Resource" not in hide:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(activity.Resource))
            root.appendChild(e)
        if "Activity" not in hide:
            for act in activity.Activity:
                e = doc.createElement("Activity")
                e.appendChild(doc.createTextNode(act))
                root.appendChild(e)

        # ComputingActivity
        if activity.Type is not None and "Type" not in hide:
            e = doc.createElement("Type")
            e.appendChild(doc.createTextNode(activity.Type))
            root.appendChild(e)
        if activity.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            e = doc.createElement("IDFromEndpoint")
            e.appendChild(doc.createTextNode(activity.IDFromEndpoint))
            root.appendChild(e)
        if activity.LocalIDFromManager is not None and "LocalIDFromManager" not in hide:
            e = doc.createElement("LocalIDFromManager")
            e.appendChild(doc.createTextNode(activity.LocalIDFromManager))
            root.appendChild(e)
        if activity.JobDescription is not None and "JobDescription" not in hide:
            e = doc.createElement("JobDescription")
            e.appendChild(doc.createTextNode(activity.JobDescription))
            root.appendChild(e)
        if activity.State is not None and "State" not in hide:
            e = doc.createElement("State")
            e.appendChild(doc.createTextNode(activity.State))
            root.appendChild(e)
        if activity.RestartState is not None and "RestartState" not in hide:
            e = doc.createElement("RestartState")
            e.appendChild(doc.createTextNode(activity.RestartState))
            root.appendChild(e)
        if activity.ExitCode is not None and "ExitCode" not in hide:
            e = doc.createElement("ExitCode")
            e.appendChild(doc.createTextNode(str(activity.ExitCode)))
            root.appendChild(e)
        if activity.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            e = doc.createElement("ComputingManagerExitCode")
            e.appendChild(doc.createTextNode(str(activity.ComputingManagerExitCode)))
            root.appendChild(e)
        if "Error" not in hide:
            for error in activity.Error:
                e = doc.createElement("Error")
                e.appendChild(doc.createTextNode(error))
                root.appendChild(e)
        if activity.WaitingPosition is not None and "WaitingPosition" not in hide:
            e = doc.createElement("WaitingPosition")
            e.appendChild(doc.createTextNode(str(activity.WaitingPosition)))
            root.appendChild(e)
        #if activity.UserDomain is not None and "UserDomain" not in hide:
        #    e = doc.createElement("UserDomain")
        #    e.appendChild(doc.createTextNode(activity.UserDomain))
        #    root.appendChild(e)
        if activity.Owner is not None and "Owner" not in hide:
            e = doc.createElement("Owner")
            e.appendChild(doc.createTextNode(activity.Owner))
            root.appendChild(e)
        if activity.LocalOwner is not None and "LocalOwner" not in hide:
            e = doc.createElement("LocalOwner")
            e.appendChild(doc.createTextNode(activity.LocalOwner))
            root.appendChild(e)
        if activity.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            e = doc.createElement("RequestedTotalWallTime")
            e.appendChild(doc.createTextNode(str(activity.RequestedTotalWallTime)))
            root.appendChild(e)
        if activity.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            e = doc.createElement("RequestedTotalCPUTime")
            e.appendChild(doc.createTextNode(str(activity.RequestedTotalCPUTime)))
            root.appendChild(e)
        if activity.RequestedSlots is not None and "RequestedSlots" not in hide:
            e = doc.createElement("RequestedSlots")
            e.appendChild(doc.createTextNode(str(activity.RequestedSlots)))
            root.appendChild(e)
        if "RequestedApplicationEnvironment" not in hide:
            for appEnv in activity.RequestedApplicationEnvironment:
                e = doc.createElement("RequestedApplicationEnvironment")
                e.appendChild(doc.createTextNode(appEnv))
                root.appendChild(e)
        if activity.StdIn is not None and "StdIn" not in hide:
            e = doc.createElement("StdIn")
            e.appendChild(doc.createTextNode(activity.StdIn))
            root.appendChild(e)
        if activity.StdOut is not None and "StdOut" not in hide:
            e = doc.createElement("StdOut")
            e.appendChild(doc.createTextNode(activity.StdOut))
            root.appendChild(e)
        if activity.StdErr is not None and "StdErr" not in hide:
            e = doc.createElement("StdErr")
            e.appendChild(doc.createTextNode(activity.StdErr))
            root.appendChild(e)
        if activity.LogDir is not None and "LogDir" not in hide:
            e = doc.createElement("LogDir")
            e.appendChild(doc.createTextNode(activity.LogDir))
            root.appendChild(e)
        if "ExecutionNode" not in hide:
            for node in activity.ExecutionNode:
                e = doc.createElement("ExecutionNode")
                e.appendChild(doc.createTextNode(node))
                root.appendChild(e)
        if activity.Queue is not None and "Queue" not in hide:
            e = doc.createElement("Queue")
            e.appendChild(doc.createTextNode(activity.Queue))
            root.appendChild(e)
        if activity.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            e = doc.createElement("UsedTotalWallTime")
            e.appendChild(doc.createTextNode(str(activity.UsedTotalWallTime)))
            root.appendChild(e)
        if activity.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            e = doc.createElement("UsedTotalCPUTime")
            e.appendChild(doc.createTextNode(str(activity.UsedTotalCPUTime)))
            root.appendChild(e)
        if activity.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            e = doc.createElement("UsedMainMemory")
            e.appendChild(doc.createTextNode(str(activity.UsedMainMemory)))
            root.appendChild(e)
        if activity.SubmissionTime is not None and "SubmissionTime" not in hide:
            e = doc.createElement("SubmissionTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.SubmissionTime)))
            root.appendChild(e)
        if activity.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            e = doc.createElement("ComputingManagerSubmissionTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.ComputingManagerSubmissionTime)))
            root.appendChild(e)
        if activity.StartTime is not None and "StartTime" not in hide:
            e = doc.createElement("StartTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.StartTime)))
            root.appendChild(e)
        if activity.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            e = doc.createElement("ComputingManagerEndTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.ComputingManagerEndTime)))
            root.appendChild(e)
        if activity.EndTime is not None and "EndTime" not in hide:
            e = doc.createElement("EndTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.EndTime)))
            root.appendChild(e)
        if activity.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            e = doc.createElement("WorkingAreaEraseTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.WorkingAreaEraseTime)))
            root.appendChild(e)
        if activity.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            e = doc.createElement("ProxyExpirationTime")
            e.appendChild(doc.createTextNode(dateTimeToText(activity.ProxyExpirationTime)))
            root.appendChild(e)
        if activity.SubmissionHost is not None and "SubmissionHost" not in hide:
            e = doc.createElement("SubmissionHost")
            e.appendChild(doc.createTextNode(activity.SubmissionHost))
            root.appendChild(e)
        if activity.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            e = doc.createElement("SubmissionClientName")
            e.appendChild(doc.createTextNode(activity.SubmissionClientName))
            root.appendChild(e)
        for message in activity.OtherMessages:
            e = doc.createElement("OtherMessages")
            e.appendChild(doc.createTextNode(message))
            root.appendChild(e)
        if activity.ComputingEndpoint is not None:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(activity.ComputingEndpoint))
            root.appendChild(e)
        if activity.ComputingShare is not None:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(activity.ComputingShare))
            root.appendChild(e)
        if activity.ExecutionEnvironment is not None:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(activity.ExecutionEnvironment))
            root.appendChild(e)

        return doc

#######################################################################################################################

class ComputingActivityIpfJson(Representation):
    data_cls = ComputingActivity

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        return json.dumps(self.toJson(self.data),sort_keys=True,indent=4)

    @staticmethod
    def toJson(activity):
        hide = activity.hide
        
        doc = {}
        
        # Entity
        doc["CreationTime"] = dateTimeToText(activity.CreationTime)
        if activity.Validity is not None:
            doc["Validity"] = activity.Validity
        doc["ID"] = activity.ID
        if activity.Name is not None and "Name" not in hide:
            doc["Name"] = activity.Name
        if len(activity.OtherInfo) > 0 and "OtherInfo" not in hide:
            doc["OtherInfo"] = activity.OtherInfo
        if len(activity.Extension) > 0 and "Extension" not in hide:
            doc["Extension"] = {}
            for name in activity.Extension:
                if isinstance(activity.Extension[name],datetime.datetime):
                    doc["Extension"][name] = dateTimeToText(activity.Extension[name])
                else:
                    doc["Extension"][name] = activity.Extension[name]

        # Activity
        if activity.UserDomain is not None and "UserDomain" not in hide:
            doc["UserDomain"] = activity.UserDomain
        if activity.Endpoint is not None and "Endpoint" not in hide:
            doc["Endpoint"] = activity.Endpoint
        if activity.Share is not None and "Share" not in hide:
            doc["Share"] = activity.Share
        if activity.Resource is not None and "Resource" not in hide:
            doc["Resource"] = activity.Resource
        if len(activity.Activity) > 0 and "Activity" not in hide:
            doc["Activity"] = activity.Activity

        # ComputingActivity
        if activity.Type is not None and "Type" not in hide:
            doc["Type"] = activity.Type
        if activity.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            doc["ActivityFromEndpoint"] = activity.IDFromEndpoint
        if activity.LocalIDFromManager is not None and "LocalIDFromManaer" not in hide:
            doc["LocalIDFromManager"] = activity.LocalIDFromManager
        if activity.JobDescription is not None and "JobDescription" not in hide:
            doc["JobDescription"] = activity.JobDescription
        if activity.State is not None and "State" not in hide:
            doc["State"] = activity.State
        if activity.RestartState is not None and "RestartState" not in hide:
            doc["RestartState"] = activity.RestartState
        if activity.ExitCode is not None and "ExitCode" not in hide:
            doc["ExitCode"] = activity.ExitCode
        if activity.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            doc["ComputingManagerExitCode"] = activity.ComputingManagerExitCode
        if len(activity.Error) > 0 and "Error" not in hide:
            doc["Error"] = activity.Error
        if activity.WaitingPosition is not None and "WaitingPosition" not in hide:
            doc["WaitingPosition"] = activity.WaitingPosition
        #if activity.UserDomain is not None and "UserDomain" not in hide:
        #    doc["UserDomain"] = UserDomain
        if activity.Owner is not None and "Owner" not in hide:
            doc["Owner"] = activity.Owner
        if activity.LocalOwner is not None and "LocalOwner" not in hide:
            doc["LocalOwner"] = activity.LocalOwner
        if activity.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            doc["RequestedTotalWallTime"] = activity.RequestedTotalWallTime
        if activity.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            doc["RequestedTotalCPUTime"] = activity.RequestedTotalCPUTime
        if activity.RequestedSlots is not None and "RequestedSlots" not in hide:
            doc["RequestedSlots"] = activity.RequestedSlots
        if len(activity.RequestedApplicationEnvironment) > 0 and "RequestedApplicationEnvironment" not in hide:
            doc["RequestedApplicationEnvironment"] = activity.RequestedApplicationEnvironment
        if activity.StdIn is not None and "StdIn" not in hide:
            doc["StdIn"] = activity.StdIn
        if activity.StdOut is not None and "StdOut" not in hide:
            doc["StdOut"] = activity.StdOut
        if activity.StdErr is not None and "StdErr" not in hide:
            doc["StdErr"] = activity.StdErr
        if activity.LogDir is not None and "LogDir" not in hide:
            doc["LogDir"] = activity.LogDir
        if len(activity.ExecutionNode) > 0 and "ExecutionNode" not in hide:
            doc["ExecutionNode"] = activity.ExecutionNode
        if activity.Queue is not None and "Queue" not in hide:
            doc["Queue"] = activity.Queue
        if activity.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            doc["UsedTotalWallTime"] = activity.UsedTotalWallTime
        if activity.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            doc["UsedTotalCPUTime"] = activity.UsedTotalCPUTime
        if activity.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            doc["UsedMainMemory"] = activity.UsedMainMemory
        if activity.SubmissionTime is not None and "SubmissionTime" not in hide:
            doc["SubmissionTime"] = dateTimeToText(activity.SubmissionTime)
        if activity.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            doc["ComputingManagerSubmissionTime"] = dateTimeToText(activity.ComputingManagerSubmissionTime)
        if activity.StartTime is not None and "StartTime" not in hide:
            doc["StartTime"] = dateTimeToText(activity.StartTime)
        if activity.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            doc["ComputingManagerEndTime"] = dateTimeToText(activity.ComputingManagerEndTime)
        if activity.EndTime is not None and "EndTime" not in hide:
            doc["EndTime"] = dateTimeToText(activity.EndTime)
        if activity.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            doc["WorkingAreaEraseTime"] = dateTimeToText(activity.WorkingAreaEraseTime)
        if activity.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            doc["ProxyExpirationTime"] = dateTimeToText(activity.ProxyExpirationTime)
        if activity.SubmissionHost is not None and "SubmissionHost" not in hide:
            doc["SubmissionHost"] = activity.SubmissionHost
        if activity.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            doc["SubmissionClientName"] = activity.SubmissionClientName
        if len(activity.OtherMessages) > 0 and "OtherMessages" not in hide:
            doc["OtherMessages"] = activity.OtherMessages
        if activity.ComputingEndpoint is not None and "ComputingEndpoint" not in hide:
            doc["ComputingEndpoint"] = activity.ComputingEndpoint
        if activity.ComputingShare is not None and "ComputingShare" not in hide:
            doc["ComputingShare"] = activity.ComputingShare
        if activity.ExecutionEnvironment is not None and "ExecutionEnvironment" not in hide:
            doc["ExecutionEnvironment"] = activity.ExecutionEnvironment

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

class ComputingActivitiesIpfJson(Representation):
    data_cls = ComputingActivities

    def __init__(self, data):
        Representation.__init__(self,Representation.MIME_APPLICATION_JSON,data)

    def get(self):
        adoc = []
        for activity in self.data.activities:
            adoc.append(ComputingActivityIpfJson.toJson(activity))
        return json.dumps(adoc,sort_keys=True,indent=4)
    
#######################################################################################################################
