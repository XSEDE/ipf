
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

# TeraGrid job states:
#
#    teragrid:pending
#    teragrid:held
#    teragrid:running
#    teragrid:terminated
#    teragrid:finished

import json    # new in Python 2.6
import time
from xml.dom.minidom import getDOMImplementation
import ConfigParser

from ipf.document import Document
from ipf.step import Step

from ipf.dt import *

#######################################################################################################################

def includeQueue(engine, queue_name, no_queue_name_return=False):
    if queue_name == None:
        return no_queue_name_return
    if queue_name == "":
        return no_queue_name_return

    try:
        expression = engine.config.get("glue2","queues")
    except ConfigParser.Error:
        return True

    toks = expression.split()
    goodSoFar = False
    for tok in toks:
        if tok[0] == '+':
            queue = tok[1:]
            if (queue == "*") or (queue == queue_name):
                goodSoFar = True
        elif tok[0] == '-':
            queue = tok[1:]
            if (queue == "*") or (queue == queue_name):
                goodSoFar = False
        else:
            engine.warning("can't parse part of Queues expression: "+tok)
    return goodSoFar

#######################################################################################################################

class ComputingActivitiesStep(Step):
    def __init__(self):
        Step.__init__(self)

        self.name = "glue2/computing_activities"
        self.description = "produces a document containing one or more GLUE 2 ComputingActivity"
        self.time_out = 30
        self.requires_types = ["ipf/resource_name.txt"]
        self.produces_types = ["glue2/teragrid/computing_activities.xml",
                               "glue2/teragrid/computing_activities.json"]

        self.resource_name = None

    def input(self, document):
        if document.type == "ipf/resource_name.txt":
            self.resource_name = document.body.rstrip()
        else:
            self.info("ignoring unwanted input "+document.type)

    def noMoreInputs(self):
        pass

    def run(self):
        self.info("waiting for ipf/resource_name.txt")
        while self.resource_name == None:
            time.sleep(0.25)

        activities = self._run()

        for activity in activities:
            activity.ID = "http://"+self.resource_name+"/glue2/ComputingActivity/"+activity.LocalIDFromManager

        hide = self._getJobAttribsToHide()
        if "glue2/teragrid/computing_activities.xml" in self.requested_types:
            self.engine.output(self,ComputingActivitiesDocumentXml(self.resource_name,activities,hide))
        if "glue2/teragrid/computing_activities.json" in self.requested_types:
            self.engine.output(self,ComputingActivitiesDocumentJson(self.resource_name,activities,hide))

    def _run(self):
        raise StepError("ComputingActivitiesStep._run not overriden")

    def _getJobAttribsToHide(self):
        hide = {}
        try:
            hideStr = self.engine.config.get("glue2","hide_job_attribs")
            for name in hideStr.split():
                hide[name] = True
        except ConfigParser.Error:
            pass
        return hide

#######################################################################################################################

class ComputingActivitiesDocumentXml(Document):
    def __init__(self, resource_name, activities, hide):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_activities.xml")
        self.activities = activities
        self.hide = hide

    def _setBody(self, body):
        raise DocumentError("ComputingActivitiesDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        for activity in self.activities:
            adoc = activity.toDom(self.hide)
            doc.documentElement.appendChild(adoc.documentElement.firstChild)
        #return doc.toxml()
        return doc.toprettyxml()

#######################################################################################################################

class ComputingActivityDocumentXml(Document):
    def __init__(self, resource_name, activity, hide):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_activity.xml")
        self.activity = activity
        self.hide = hide

    def _setBody(self, body):
        raise DocumentError("ComputingActivityDocumentXml._setBody should parse the XML...")

    def _getBody(self):
        return self.activity.toDom(self.hide).toxml()

#######################################################################################################################

class ComputingActivitiesDocumentJson(Document):
    def __init__(self, resource_name, activities, hide):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_activities.json")
        self.activities = activities
        self.hide = hide

    def _setBody(self, body):
        raise DocumentError("ComputingActivitivitiesDocumentJson._setBody should parse the JSON...")

    def _getBody(self):
        adoc = []
        for activity in self.activities:
            adoc.append(activity.toJson(self.hide))
        return json.dumps(adoc,sort_keys=True,indent=4)

#######################################################################################################################

class ComputingActivityDocumentJson(Document):
    def __init__(self, resource_name, activity, hide):
        Document.__init__(self, resource_name, "glue2/teragrid/computing_activity.json")
        self.activity = activity
        self.hide = hide

    def _setBody(self, body):
        raise DocumentError("ComputingActivityDocumentJson._setBody should parse the JSON...")

    def _getBody(self):
        return json.dumps(self.activity.toJson(self.hide))

#######################################################################################################################
    
class ComputingActivity(object):
    def __init__(self):
        # Entity
        self.CreationTime = datetime.datetime.now(tzoffset(0))
        self.Validity = 300
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
        self.ComputingEndpoint = []                # list of uri
        self.ComputingShare = []                   # list of string (LocalID)
        self.ExecutionEnvironment = []             # list of uri

    ###################################################################################################################

    def toDom(self, hide):
        doc = getDOMImplementation().createDocument("http://info.teragrid.org/glue/2009/02/spec_2.0_r02",
                                                    "Entities",None)
        root = doc.createElement("ComputingActivity")
        doc.documentElement.appendChild(root)

        # Entity
        e = doc.createElement("CreationTime")
        e.appendChild(doc.createTextNode(dateTimeToText(self.CreationTime)))
        e.setAttribute("Validity",str(self.Validity))
        root.appendChild(e)

        e = doc.createElement("ID")
        e.appendChild(doc.createTextNode(self.ID))
        root.appendChild(e)

        if self.Name is not None and "Name" not in hide:
            e = doc.createElement("Name")
            e.appendChild(doc.createTextNode(self.Name))
            root.appendChild(e)
        for info in self.OtherInfo:
            e = doc.createElement("OtherInfo")
            e.appendChild(doc.createTextNode(info))
            root.appendChild(e)
        if "Extension" not in hide:
            for key in self.Extension.keys():
                e = doc.createElement("Extension")
                e.setAttribute("Key",key)
                e.appendChild(doc.createTextNode(self.Extension[key]))
                root.appendChild(e)

        # Activity
        if self.UserDomain is not None and "UserDomain" not in hide:
            e = doc.createElement("UserDomain")
            e.appendChild(doc.createTextNode(self.UserDomain))
            root.appendChild(e)
        if self.Endpoint is not None and "Endpoint" not in hide:
            e = doc.createElement("Endpoint")
            e.appendChild(doc.createTextNode(self.Endpoint))
            root.appendChild(e)
        if self.Share is not None and "Share" not in hide:
            e = doc.createElement("Share")
            e.appendChild(doc.createTextNode(self.Share))
            root.appendChild(e)
        if self.Resource is not None and "Resource" not in hide:
            e = doc.createElement("Resource")
            e.appendChild(doc.createTextNode(self.Resource))
            root.appendChild(e)
        if "Activity" not in hide:
            for act in self.Activity:
                e = doc.createElement("Activity")
                e.appendChild(doc.createTextNode(act))
                root.appendChild(e)

        # ComputingActivity
        if self.Type is not None and "Type" not in hide:
            e = doc.createElement("Type")
            e.appendChild(doc.createTextNode(self.Type))
            root.appendChild(e)
        if self.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            e = doc.createElement("IDFromEndpoint")
            e.appendChild(doc.createTextNode(self.IDFromEndpoint))
            root.appendChild(e)
        if self.LocalIDFromManager is not None and "LocalIDFromManager" not in hide:
            e = doc.createElement("LocalIDFromManager")
            e.appendChild(doc.createTextNode(self.LocalIDFromManager))
            root.appendChild(e)
        if self.JobDescription is not None and "JobDescription" not in hide:
            e = doc.createElement("JobDescription")
            e.appendChild(doc.createTextNode(self.JobDescription))
            root.appendChild(e)
        if self.State is not None and "State" not in hide:
            e = doc.createElement("State")
            e.appendChild(doc.createTextNode(self.State))
            root.appendChild(e)
        if self.RestartState is not None and "RestartState" not in hide:
            e = doc.createElement("RestartState")
            e.appendChild(doc.createTextNode(self.RestartState))
            root.appendChild(e)
        if self.ExitCode is not None and "ExitCode" not in hide:
            e = doc.createElement("ExitCode")
            e.appendChild(doc.createTextNode(str(self.ExitCode)))
            root.appendChild(e)
        if self.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            e = doc.createElement("ComputingManagerExitCode")
            e.appendChild(doc.createTextNode(str(self.ComputingManagerExitCode)))
            root.appendChild(e)
        if "Error" not in hide:
            for error in self.Error:
                e = doc.createElement("Error")
                e.appendChild(doc.createTextNode(error))
                root.appendChild(e)
        if self.WaitingPosition is not None and "WaitingPosition" not in hide:
            e = doc.createElement("WaitingPosition")
            e.appendChild(doc.createTextNode(str(self.WaitingPosition)))
            root.appendChild(e)
        #if self.UserDomain is not None and "UserDomain" not in hide:
        #    e = doc.createElement("UserDomain")
        #    e.appendChild(doc.createTextNode(self.UserDomain))
        #    root.appendChild(e)
        if self.Owner is not None and "Owner" not in hide:
            e = doc.createElement("Owner")
            e.appendChild(doc.createTextNode(self.Owner))
            root.appendChild(e)
        if self.LocalOwner is not None and "LocalOwner" not in hide:
            e = doc.createElement("LocalOwner")
            e.appendChild(doc.createTextNode(self.LocalOwner))
            root.appendChild(e)
        if self.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            e = doc.createElement("RequestedTotalWallTime")
            e.appendChild(doc.createTextNode(str(self.RequestedTotalWallTime)))
            root.appendChild(e)
        if self.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            e = doc.createElement("RequestedTotalCPUTime")
            e.appendChild(doc.createTextNode(str(self.RequestedTotalCPUTime)))
            root.appendChild(e)
        if self.RequestedSlots is not None and "RequestedSlots" not in hide:
            e = doc.createElement("RequestedSlots")
            e.appendChild(doc.createTextNode(str(self.RequestedSlots)))
            root.appendChild(e)
        if "RequestedApplicationEnvironment" not in hide:
            for appEnv in self.RequestedApplicationEnvironment:
                e = doc.createElement("RequestedApplicationEnvironment")
                e.appendChild(doc.createTextNode(appEnv))
                root.appendChild(e)
        if self.StdIn is not None and "StdIn" not in hide:
            e = doc.createElement("StdIn")
            e.appendChild(doc.createTextNode(self.StdIn))
            root.appendChild(e)
        if self.StdOut is not None and "StdOut" not in hide:
            e = doc.createElement("StdOut")
            e.appendChild(doc.createTextNode(self.StdOut))
            root.appendChild(e)
        if self.StdErr is not None and "StdErr" not in hide:
            e = doc.createElement("StdErr")
            e.appendChild(doc.createTextNode(self.StdErr))
            root.appendChild(e)
        if self.LogDir is not None and "LogDir" not in hide:
            e = doc.createElement("LogDir")
            e.appendChild(doc.createTextNode(self.LogDir))
            root.appendChild(e)
        if "ExecutionNode" not in hide:
            for node in self.ExecutionNode:
                e = doc.createElement("ExecutionNode")
                e.appendChild(doc.createTextNode(self.ExecutionNode))
                root.appendChild(e)
        if self.Queue is not None and "Queue" not in hide:
            e = doc.createElement("Queue")
            e.appendChild(doc.createTextNode(self.Queue))
            root.appendChild(e)
        if self.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            e = doc.createElement("UsedTotalWallTime")
            e.appendChild(doc.createTextNode(str(self.UsedTotalWallTime)))
            root.appendChild(e)
        if self.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            e = doc.createElement("UsedTotalCPUTime")
            e.appendChild(doc.createTextNode(str(self.UsedTotalCPUTime)))
            root.appendChild(e)
        if self.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            e = doc.createElement("UsedMainMemory")
            e.appendChild(doc.createTextNode(str(self.UsedMainMemory)))
            root.appendChild(e)
        if self.SubmissionTime is not None and "SubmissionTime" not in hide:
            e = doc.createElement("SubmissionTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.SubmissionTime)))
            root.appendChild(e)
        if self.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            e = doc.createElement("ComputingManagerSubmissionTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.ComputingManagerSubmissionTime)))
            root.appendChild(e)
        if self.StartTime is not None and "StartTime" not in hide:
            e = doc.createElement("StartTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.StartTime)))
            root.appendChild(e)
        if self.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            e = doc.createElement("ComputingManagerEndTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.ComputingManagerEndTime)))
            root.appendChild(e)
        if self.EndTime is not None and "EndTime" not in hide:
            e = doc.createElement("EndTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.EndTime)))
            root.appendChild(e)
        if self.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            e = doc.createElement("WorkingAreaEraseTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.WorkingAreaEraseTime)))
            root.appendChild(e)
        if self.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            e = doc.createElement("ProxyExpirationTime")
            e.appendChild(doc.createTextNode(dateTimeToText(self.ProxyExpirationTime)))
            root.appendChild(e)
        if self.SubmissionHost is not None and "SubmissionHost" not in hide:
            e = doc.createElement("SubmissionHost")
            e.appendChild(doc.createTextNode(self.SubmissionHost))
            root.appendChild(e)
        if self.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            e = doc.createElement("SubmissionClientName")
            e.appendChild(doc.createTextNode(self.SubmissionClientName))
            root.appendChild(e)
        for message in self.OtherMessages:
            e = doc.createElement("OtherMessages")
            e.appendChild(doc.createTextNode(message))
            root.appendChild(e)
        for endpoint in self.ComputingEndpoint:
            e = doc.createElement("ComputingEndpoint")
            e.appendChild(doc.createTextNode(endpoint))
            root.appendChild(e)
        for share in self.ComputingShare:
            e = doc.createElement("ComputingShare")
            e.appendChild(doc.createTextNode(share))
            root.appendChild(e)
        for execEnv in self.ExecutionEnvironment:
            e = doc.createElement("ExecutionEnvironment")
            e.appendChild(doc.createTextNode(execEnv))
            root.appendChild(e)

        return doc
    
    ###################################################################################################################

    def toJson(self, hide):
        doc = {}

        # Entity
        doc["CreationTime"] = dateTimeToText(self.CreationTime)
        doc["Validity"] = self.Validity
        doc["ID"] = self.ID
        if self.Name is not None and "Name" not in hide:
            doc["Name"] = self.Name
        if len(self.OtherInfo) > 0 and "OtherInfo" not in hide:
            doc["OtherInfo"] = self.OtherInfo
        if len(self.Extension) > 0 and "Extension" not in hide:
            doc["Extension"] = self.Extension

        # Activity
        if self.UserDomain is not None and "UserDomain" not in hide:
            doc["UserDomain"] = self.UserDomain
        if self.Endpoint is not None and "Endpoint" not in hide:
            doc["Endpoint"] = self.Endpoint
        if self.Share is not None and "Share" not in hide:
            doc["Share"] = self.Share
        if self.Resource is not None and "Resource" not in hide:
            doc["Resource"] = self.Resource
        if len(self.Activity) > 0 and "Activity" not in hide:
            doc["Activity"] = self.Activity

        # ComputingActivity
        if self.Type is not None and "Type" not in hide:
            doc["Type"] = self.Type
        if self.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            doc["ActivityFromEndpoint"] = self.IDFromEndpoint
        if self.LocalIDFromManager is not None and "LocalIDFromManaer" not in hide:
            doc["LocalIDFromManager"] = self.LocalIDFromManager
        if self.JobDescription is not None and "JobDescription" not in hide:
            doc["JobDescription"] = self.JobDescription
        if self.State is not None and "State" not in hide:
            doc["State"] = self.State
        if self.RestartState is not None and "RestartState" not in hide:
            doc["RestartState"] = self.RestartState
        if self.ExitCode is not None and "ExitCode" not in hide:
            doc["ExitCode"] = self.ExitCode
        if self.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            doc["ComputingManagerExitCode"] = self.ComputingManagerExitCode
        if len(self.Error) > 0 and "Error" not in hide:
            doc["Error"] = self.Error
        if self.WaitingPosition is not None and "WaitingPosition" not in hide:
            doc["WaitingPosition"] = self.WaitingPosition
        #if self.UserDomain is not None and "UserDomain" not in hide:
        #    doc["UserDomain"] = UserDomain
        if self.Owner is not None and "Owner" not in hide:
            doc["Owner"] = self.Owner
        if self.LocalOwner is not None and "LocalOwner" not in hide:
            doc["LocalOwner"] = self.LocalOwner
        if self.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            doc["RequestedTotalWallTime"] = self.RequestedTotalWallTime
        if self.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            doc["RequestedTotalCPUTime"] = self.RequestedTotalCPUTime
        if self.RequestedSlots is not None and "RequestedSlots" not in hide:
            doc["RequestedSlots"] = self.RequestedSlots
        if len(self.RequestedApplicationEnvironment) > 0 and "RequestedApplicationEnvironment" not in hide:
            doc["RequestedApplicationEnvironment"] = self.RequestedApplicationEnvironment
        if self.StdIn is not None and "StdIn" not in hide:
            doc["StdIn"] = self.StdIn
        if self.StdOut is not None and "StdOut" not in hide:
            doc["StdOut"] = self.StdOut
        if self.StdErr is not None and "StdErr" not in hide:
            doc["StdErr"] = self.StdErr
        if self.LogDir is not None and "LogDir" not in hide:
            doc["LogDir"] = self.LogDir
        if len(self.ExecutionNode) > 0 and "ExecutionNode" not in hide:
            doc["ExecutionNode"] = self.ExecutionNode
        if self.Queue is not None and "Queue" not in hide:
            doc["Queue"] = self.Queue
        if self.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            doc["UsedTotalWallTime"] = self.UsedTotalWallTime
        if self.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            doc["UsedTotalCPUTime"] = self.UsedTotalCPUTime
        if self.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            doc["UsedMainMemory"] = self.UsedMainMemory
        if self.SubmissionTime is not None and "SubmissionTime" not in hide:
            doc["SubmissionTime"] = dateTimeToText(self.SubmissionTime)
        if self.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            doc["ComputingManagerSubmissionTime"] = dateTimeToText(self.ComputingManagerSubmissionTime)
        if self.StartTime is not None and "StartTime" not in hide:
            doc["StartTime"] = dateTimeToText(self.StartTime)
        if self.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            doc["ComputingManagerEndTime"] = dateTimeToText(self.ComputingManagerEndTime)
        if self.EndTime is not None and "EndTime" not in hide:
            doc["EndTime"] = dateTimeToText(self.EndTime)
        if self.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            doc["WorkingAreaEraseTime"] = dateTimeToText(self.WorkingAreaEraseTime)
        if self.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            doc["ProxyExpirationTime"] = dateTimeToText(self.ProxyExpirationTime)
        if self.SubmissionHost is not None and "SubmissionHost" not in hide:
            doc["SubmissionHost"] = self.SubmissionHost
        if self.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            doc["SubmissionClientName"] = self.SubmissionClientName
        if len(self.OtherMessages) > 0 and "OtherMessages" not in hide:
            doc["OtherMessages"] = self.OtherMessages
        if len(self.ComputingEndpoint) > 0 and "ComputingEndpoint" not in hide:
            doc["ComputingEndpoint"] = self.ComputingEndpoint
        if len(self.ComputingShare) > 0 and "ComputingShare" not in hide:
            doc["ComputingShare"] = self.ComputingShare
        if len(self.ExecutionEnvironment) > 0 and "ExecutionEnvironment" not in hide:
            doc["ExecutionEnvironment"] = self.ExecutionEnvironment

        return doc
    
    ###################################################################################################################

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

    ###################################################################################################################

    def toXml(self, hide, indent=""):
        mstr = ""
        #mstr = mstr+"<?xml version='1.0' encoding='UTF-8'?>\n"
        #mstr = mstr+indent+"<Entities xmlns='http://info.teragrid.org/glue/2009/02/spec_2.0_r01'>\n"

        mstr = mstr+indent+"<ComputingActivity"

        # Entity
        mstr = mstr+" CreationTime='"+dateTimeToText(self.CreationTime)+"'\n"
        mstr = mstr+indent+("                   Validity='%d'>\n" % self.Validity)
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name is not None and "Name" not in hide:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        if "Extension" not in hide:
            for key in self.Extension.keys():
                mstr = mstr+indent+"  <Extension Key='"+key+"'>"+self.Extension[key]+"</Extension>\n"

        # Activity
        if self.UserDomain is not None and "UserDomain" not in hide:
            mstr = mstr+indent+"  <UserDomain>"+self.UserDomain+"</UserDomain>\n"
        if self.Endpoint is not None and "Endpoint" not in hide:
            mstr = mstr+indent+"  <Endpoint>"+self.Endpoint+"</Endpoint>\n"
        if self.Share is not None and "Share" not in hide:
            mstr = mstr+indent+"  <Share>"+self.Share+"</Share>\n"
        if self.Resource is not None and "Resource" not in hide:
            mstr = mstr+indent+"  <Resource>"+self.Resource+"</Resource>\n"
        if "Activity" not in hide:
            for act in self.Activity:
                mstr = mstr+indent+"  <Activity>"+act+"</Activity>\n"

        # ComputingActivity
        if self.Type is not None and "Type" not in hide:
            mstr = mstr+indent+"  <Type>"+self.Type+"</Type>\n"
        if self.IDFromEndpoint is not None and "IDFromEndpoint" not in hide:
            mstr = mstr+indent+"  <IDFromEndpoint>"+self.IDFromEndpoint+"</IDFromEndpoint>\n"
        if self.LocalIDFromManager is not None and "LocalIDFromManaer" not in hide:
            mstr = mstr+indent+"  <LocalIDFromManager>"+self.LocalIDFromManager+"</LocalIDFromManager>\n"
        if self.JobDescription is not None and "JobDescription" not in hide:
            mstr = mstr+indent+"  <JobDescription>"+self.JobDescription+"</JobDescription>\n"
        if self.State is not None and "State" not in hide:
            mstr = mstr+indent+"  <State>"+self.State+"</State>\n"
        if self.RestartState is not None and "RestartState" not in hide:
            mstr = mstr+indent+"  <RestartState>"+self.RestartState+"</RestartState>\n"
        if self.ExitCode is not None and "ExitCode" not in hide:
            mstr = mstr+indent+"  <ExitCode>"+str(self.ExitCode)+"</ExitCode>\n"
        if self.ComputingManagerExitCode is not None and "ComputingManagerExitCode" not in hide:
            mstr = mstr+indent+"  <ComputingManagerExitCode>"+str(self.ComputingManagerExitCode)+ \
                   "</ComputingManagerExitCode>\n"
        if "Error" not in hide:
            for error in self.Error:
                mstr = mstr+indent+"  <Error>"+error+"</Error>\n"
        if self.WaitingPosition is not None and "WaitingPosition" not in hide:
            mstr = mstr+indent+"  <WaitingPosition>"+str(self.WaitingPosition)+"</WaitingPosition>\n"
        #if self.UserDomain is not None and "UserDomain" not in hide:
        #    mstr = mstr+indent+"  <UserDomain>"+self.UserDomain+"</UserDomain>\n"
        if self.Owner is not None and "Owner" not in hide:
            mstr = mstr+indent+"  <Owner>"+self.Owner+"</Owner>\n"
        if self.LocalOwner is not None and "LocalOwner" not in hide:
            mstr = mstr+indent+"  <LocalOwner>"+self.LocalOwner+"</LocalOwner>\n"
        if self.RequestedTotalWallTime is not None and "RequestedTotalWallTime" not in hide:
            mstr = mstr+indent+"  <RequestedTotalWallTime>"+str(self.RequestedTotalWallTime)+ \
                   "</RequestedTotalWallTime>\n"
        if self.RequestedTotalCPUTime is not None and "RequestedTotalCPUTime" not in hide:
            mstr = mstr+indent+"  <RequestedTotalCPUTime>"+str(self.RequestedTotalCPUTime)+ \
                   "</RequestedTotalCPUTime>\n"
        if self.RequestedSlots is not None and "RequestedSlots" not in hide:
            mstr = mstr+indent+"  <RequestedSlots>"+str(self.RequestedSlots)+"</RequestedSlots>\n"
        if "RequestedApplicationEnvironment" not in hide:
            for appEnv in self.RequestedApplicationEnvironment:
                mstr = mstr+indent+"  <RequestedApplicationEnvironment>"+appEnv+"</RequestedApplicationEnvironment>\n"
        if self.StdIn is not None and "StdIn" not in hide:
            mstr = mstr+indent+"  <StdIn>"+self.StdIn+"</StdIn>\n"
        if self.StdOut is not None and "StdOut" not in hide:
            mstr = mstr+indent+"  <StdOut>"+self.StdOut+"</StdOut>\n"
        if self.StdErr is not None and "StdErr" not in hide:
            mstr = mstr+indent+"  <StdErr>"+self.StdErr+"</StdErr>\n"
        if self.LogDir is not None and "LogDir" not in hide:
            mstr = mstr+indent+"  <LogDir>"+self.LogDir+"</LogDir>\n"
        if "ExecutionNode" not in hide:
            for node in self.ExecutionNode:
                mstr = mstr+indent+"  <ExecutionNode>"+node+"</ExecutionNode>\n"
        if self.Queue is not None and "Queue" not in hide:
            mstr = mstr+indent+"  <Queue>"+self.Queue+"</Queue>\n"
        if self.UsedTotalWallTime is not None and "UsedTotalWallTime" not in hide:
            mstr = mstr+indent+"  <UsedTotalWallTime>"+str(self.UsedTotalWallTime)+"</UsedTotalWallTime>\n"
        if self.UsedTotalCPUTime is not None and "UsedTotalCPUTime" not in hide:
            mstr = mstr+indent+"  <UsedTotalCPUTime>"+str(self.UsedTotalCPUTime)+"</UsedTotalCPUTime>\n"
        if self.UsedMainMemory is not None and "UsedMainMemory" not in hide:
            mstr = mstr+indent+"  <UsedMainMemory>"+str(self.UsedMainMemory)+"</UsedMainMemory>\n"
        if self.SubmissionTime is not None and "SubmissionTime" not in hide:
            mstr = mstr+indent+"  <SubmissionTime>"+dateTimeToText(self.SubmissionTime)+ \
                   "</SubmissionTime>\n" #?
        if self.ComputingManagerSubmissionTime is not None and "ComputingManagerSubmissionTime" not in hide:
            mstr = mstr+indent+"  <ComputingManagerSubmissionTime>"+ \
                   dateTimeToText(self.ComputingManagerSubmissionTime)+ \
                   "</ComputingManagerSubmissionTime>\n" #?
        if self.StartTime is not None and "StartTime" not in hide:
            mstr = mstr+indent+"  <StartTime>"+dateTimeToText(self.StartTime)+"</StartTime>\n" #?
        if self.ComputingManagerEndTime is not None and "ComputingManagerEndTime" not in hide:
            mstr = mstr+indent+"  <ComputingManagerEndTime>"+dateTimeToText(self.ComputingManagerEndTime)+\
                   "</ComputingManagerEndTime>\n" #?
        if self.EndTime is not None and "EndTime" not in hide:
            mstr = mstr+indent+"  <EndTime>"+dateTimeToText(self.EndTime)+"</EndTime>\n" #?
        if self.WorkingAreaEraseTime is not None and "WorkingAreaEraseTime" not in hide:
            mstr = mstr+indent+"  <WorkingAreaEraseTime>"+dateTimeToText(self.WorkingAreaEraseTime)+ \
                   "</WorkingAreaEraseTime>\n" #?
        if self.ProxyExpirationTime is not None and "ProxyExpirationTime" not in hide:
            mstr = mstr+indent+"  <ProxyExpirationTime>"+dateTimeToText(self.ProxyExpirationTime)+ \
                   "</ProxyExpirationTime>\n" #?
        if self.SubmissionHost is not None and "SubmissionHost" not in hide:
            mstr = mstr+indent+"  <SubmissionHost>"+self.SubmissionHost+"</SubmissionHost>\n"
        if self.SubmissionClientName is not None and "SubmissionClientName" not in hide:
            mstr = mstr+indent+"  <SubmissionClientName>"+self.SubmissionClientName+"</SubmissionClientName>\n"
        for message in self.OtherMessages:
            mstr = mstr+indent+"  <OtherMessages>"+message+"</OtherMessages>\n"
        for endpoint in self.ComputingEndpoint:
            mstr = mstr+indent+"  <ComputingEndpoint>"+endpoint+"</ComputingEndpoint>\n"
        for share in self.ComputingShare:
            mstr = mstr+indent+"  <ComputingShare>"+share+"</ComputingShare>\n"
        for execEnv in self.ExecutionEnvironment:
            mstr = mstr+indent+"  <ExecutionEnvironment>"+execEnv+"</ExecutionEnvironment>\n"
        mstr = mstr+indent+"</ComputingActivity>\n"

        #mstr = mstr + "</Entities>\n"
        return mstr
    
#######################################################################################################################
