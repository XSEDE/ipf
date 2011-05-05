
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

# TeraGrid job states:
#
#    teragrid:pending
#    teragrid:held
#    teragrid:running
#    teragrid:terminated
#    teragrid:finished

import time
import ConfigParser

from ipf.document import Document
from teragrid.tgagent import TeraGridAgent
from teragrid.xmlhelper import *

##############################################################################################################

def includeQueue(config, queue_name, no_queue_name_return=False):
    if queue_name == None:
        return no_queue_name_return
    if queue_name == "":
        return no_queue_name_return

    try:
        expression = config.get("glue2","queues")
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
            logger.warn("can't parse part of Queues expression: "+tok)
    return goodSoFar

##############################################################################################################

class ComputingActivitiesAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)
        self.description = "This agent provides documents in the GLUE 2 ComputingActivity schema. For a batch scheduled system, these are typically jobs."
        self.default_timeout = 60
        self.hide = self._getJobAttribsToHide()

    def _getJobAttribsToHide(self):
        hide = {}
        try:
            hideStr = self.config.get("glue2","hide_job_attribs")
            for name in hideStr.split():
                hide[name] = True
        except ConfigParser.Error:
            pass
        return hide

##############################################################################################################
    
class ComputingActivity(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.ComputingActivity"
        self.content_type = "text/xml"

        self.hide = {}

        # Entity
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
        #self.UserDomain = None
        self.Owner = None                          # string
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

        # required attributes that may be forgotten
        self.Owner = "unknown"

    def _setBody(self, body):
        logger.info("ComputingActivity._setBody should parse the XML...")

    def _getBody(self):
        return self._toXml()
    
    def _toXml(self, indent=""):
        mstr = ""
        #mstr = mstr+"<?xml version='1.0' encoding='UTF-8'?>\n"
        #mstr = mstr+indent+"<Entities xmlns='http://info.teragrid.org/glue/2009/02/spec_2.0_r01'>\n"

        mstr = mstr+indent+"<ComputingActivity"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                   Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name != None and "Name" not in self.hide:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        if "Extension" not in self.hide:
            for key in self.Extension.keys():
                mstr = mstr+indent+"  <Extension Key='"+key+"'>"+self.Extension[key]+"</Extension>\n"

        # Activity
        if self.UserDomain != None and "UserDomain" not in self.hide:
            mstr = mstr+indent+"  <UserDomain>"+self.UserDomain+"</UserDomain>\n"
        if self.Endpoint != None and "Endpoint" not in self.hide:
            mstr = mstr+indent+"  <Endpoint>"+self.Endpoint+"</Endpoint>\n"
        if self.Share != None and "Share" not in self.hide:
            mstr = mstr+indent+"  <Share>"+self.Share+"</Share>\n"
        if self.Resource != None and "Resource" not in self.hide:
            mstr = mstr+indent+"  <Resource>"+self.Resource+"</Resource>\n"
        if "Activity" not in self.hide:
            for activity in self.Activity:
                mstr = mstr+indent+"  <Activity>"+activity+"</Activity>\n"

        # ComputingActivity
        if self.Type != None and "Type" not in self.hide:
            mstr = mstr+indent+"  <Type>"+self.Type+"</Type>\n"
        if self.IDFromEndpoint != None and "IDFromEndpoint" not in self.hide:
            mstr = mstr+indent+"  <IDFromEndpoint>"+self.IDFromEndpoint+"</IDFromEndpoint>\n"
        if self.LocalIDFromManager != None and "LocalIDFromManaer" not in self.hide:
            mstr = mstr+indent+"  <LocalIDFromManager>"+self.LocalIDFromManager+"</LocalIDFromManager>\n"
        if self.JobDescription != None and "JobDescription" not in self.hide:
            mstr = mstr+indent+"  <JobDescription>"+self.JobDescription+"</JobDescription>\n"
        if self.State != None and "State" not in self.hide:
            mstr = mstr+indent+"  <State>"+self.State+"</State>\n"
        if self.RestartState != None and "RestartState" not in self.hide:
            mstr = mstr+indent+"  <RestartState>"+self.RestartState+"</RestartState>\n"
        if self.ExitCode != None and "ExitCode" not in self.hide:
            mstr = mstr+indent+"  <ExitCode>"+str(self.ExitCode)+"</ExitCode>\n"
        if self.ComputingManagerExitCode != None and "ComputingManagerExitCode" not in self.hide:
            mstr = mstr+indent+"  <ComputingManagerExitCode>"+str(self.ComputingManagerExitCode)+ \
                   "</ComputingManagerExitCode>\n"
        if "Error" not in self.hide:
            for error in self.Error:
                mstr = mstr+indent+"  <Error>"+error+"</Error>\n"
        if self.WaitingPosition != None and "WaitingPosition" not in self.hide:
            mstr = mstr+indent+"  <WaitingPosition>"+str(self.WaitingPosition)+"</WaitingPosition>\n"
        #if self.UserDomain != None and "UserDomain" not in self.hide:
        #    mstr = mstr+indent+"  <UserDomain>"+self.UserDomain+"</UserDomain>\n"
        if self.Owner != None and "Owner" not in self.hide:
            mstr = mstr+indent+"  <Owner>"+self.Owner+"</Owner>\n"
        if self.LocalOwner != None and "LocalOwner" not in self.hide:
            mstr = mstr+indent+"  <LocalOwner>"+self.LocalOwner+"</LocalOwner>\n"
        if self.RequestedTotalWallTime != None and "RequestedTotalWallTime" not in self.hide:
            mstr = mstr+indent+"  <RequestedTotalWallTime>"+str(self.RequestedTotalWallTime)+ \
                   "</RequestedTotalWallTime>\n"
        if self.RequestedTotalCPUTime != None and "RequestedTotalCPUTime" not in self.hide:
            mstr = mstr+indent+"  <RequestedTotalCPUTime>"+str(self.RequestedTotalCPUTime)+ \
                   "</RequestedTotalCPUTime>\n"
        if self.RequestedSlots != None and "RequestedSlots" not in self.hide:
            mstr = mstr+indent+"  <RequestedSlots>"+str(self.RequestedSlots)+"</RequestedSlots>\n"
        if "RequestedApplicationEnvironment" not in self.hide:
            for appEnv in self.RequestedApplicationEnvironment:
                mstr = mstr+indent+"  <RequestedApplicationEnvironment>"+appEnv+"</RequestedApplicationEnvironment>\n"
        if self.StdIn != None and "StdIn" not in self.hide:
            mstr = mstr+indent+"  <StdIn>"+self.StdIn+"</StdIn>\n"
        if self.StdOut != None and "StdOut" not in self.hide:
            mstr = mstr+indent+"  <StdOut>"+self.StdOut+"</StdOut>\n"
        if self.StdErr != None and "StdErr" not in self.hide:
            mstr = mstr+indent+"  <StdErr>"+self.StdErr+"</StdErr>\n"
        if self.LogDir != None and "LogDir" not in self.hide:
            mstr = mstr+indent+"  <LogDir>"+self.LogDir+"</LogDir>\n"
        if "ExecutionNode" not in self.hide:
            for node in self.ExecutionNode:
                mstr = mstr+indent+"  <ExecutionNode>"+node+"</ExecutionNode>\n"
        if self.Queue != None and "Queue" not in self.hide:
            mstr = mstr+indent+"  <Queue>"+self.Queue+"</Queue>\n"
        if self.UsedTotalWallTime != None and "UsedTotalWallTime" not in self.hide:
            mstr = mstr+indent+"  <UsedTotalWallTime>"+str(self.UsedTotalWallTime)+"</UsedTotalWallTime>\n"
        if self.UsedTotalCPUTime != None and "UsedTotalCPUTime" not in self.hide:
            mstr = mstr+indent+"  <UsedTotalCPUTime>"+str(self.UsedTotalCPUTime)+"</UsedTotalCPUTime>\n"
        if self.UsedMainMemory != None and "UsedMainMemory" not in self.hide:
            mstr = mstr+indent+"  <UsedMainMemory>"+str(self.UsedMainMemory)+"</UsedMainMemory>\n"
        if self.SubmissionTime != None and "SubmissionTime" not in self.hide:
            mstr = mstr+indent+"  <SubmissionTime>"+self._glueFormat(self.SubmissionTime)+"</SubmissionTime>\n" #?
        if self.ComputingManagerSubmissionTime != None and "ComputingManagerSubmissionTime" not in self.hide:
            mstr = mstr+indent+"  <ComputingManagerSubmissionTime>"+\
                   self._glueFormat(self.ComputingManagerSubmissionTime)+"</ComputingManagerSubmissionTime>\n" #?
        if self.StartTime != None and "StartTime" not in self.hide:
            mstr = mstr+indent+"  <StartTime>"+self._glueFormat(self.StartTime)+"</StartTime>\n" #?
        if self.ComputingManagerEndTime != None and "ComputingManagerEndTime" not in self.hide:
            mstr = mstr+indent+"  <ComputingManagerEndTime>"+self._glueFormat(self.ComputingManagerEndTime)+\
                   "</ComputingManagerEndTime>\n" #?
        if self.EndTime != None and "EndTime" not in self.hide:
            mstr = mstr+indent+"  <EndTime>"+self._glueFormat(self.EndTime)+"</EndTime>\n" #?
        if self.WorkingAreaEraseTime != None and "WorkingAreaEraseTime" not in self.hide:
            mstr = mstr+indent+"  <WorkingAreaEraseTime>"+self._glueFormat(self.WorkingAreaEraseTime)+ \
                   "</WorkingAreaEraseTime>\n" #?
        if self.ProxyExpirationTime != None and "ProxyExpirationTime" not in self.hide:
            mstr = mstr+indent+"  <ProxyExpirationTime>"+self._glueFormat(self.ProxyExpirationTime)+ \
                   "</ProxyExpirationTime>\n" #?
        if self.SubmissionHost != None and "SubmissionHost" not in self.hide:
            mstr = mstr+indent+"  <SubmissionHost>"+self.SubmissionHost+"</SubmissionHost>\n"
        if self.SubmissionClientName != None and "SubmissionClientName" not in self.hide:
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

    def _glueFormat(self, dt):
        dt = dt - dt.utcoffset()
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
