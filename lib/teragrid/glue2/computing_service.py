
###############################################################################
#   Copyright 2009 The University of Texas at Austin                          #
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

import time

from ipf.document import Document
from teragrid.agent import TeraGridAgent
from teragrid.xmlhelper import *

##############################################################################################################

class ComputingServiceAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)
        self.description = "This agent provides documents in the GLUE 2 ComputingService schema. It is an aggregation mechanism"
        self.default_timeout = 30

    def _addShare(self, service, share):
        service.ComputingShare.append(share.ID)
        if share.TotalJobs != None:
            if service.TotalJobs == None:
                service.TotalJobs = 0
            service.TotalJobs = service.TotalJobs + share.TotalJobs
        if share.RunningJobs != None:
            if service.RunningJobs == None:
                service.RunningJobs = 0
            service.RunningJobs = service.RunningJobs + share.RunningJobs
        if share.WaitingJobs != None:
            if service.WaitingJobs == None:
                service.WaitingJobs = 0
            service.WaitingJobs = service.WaitingJobs + share.WaitingJobs
        if share.StagingJobs != None:
            if service.StagingJobs == None:
                service.StagingJobs = 0
            service.StagingJobs = service.StagingJobs + share.StagingJobs
        if share.SuspendedJobs != None:
            if service.SuspendedJobs == None:
                service.SuspendedJobs = 0
            service.SuspendedJobs = service.SuspendedJobs + share.SuspendedJobs
        if share.PreLRMSWaitingJobs != None:
            if service.PreLRMSWaitingJobs == None:
                service.PreLRMSWaitingJobs = 0
            service.PreLRMSWaitingJobs = service.PreLRMSWaitingJobs + share.PreLRMSWaitingJobs

##############################################################################################################

class ComputingService(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.ComputingService"
        self.content_type = "text/xml"

        # Entity
        self.ID = None
        self.Name = None
        self.OtherInfo = [] # strings
        self.Extension = {} # (key,value) strings

        # Service
        self.Capability = None   # string (Capability)
        self.Type = None         # string (ServiceType)
        self.QualityLevel = None # string (QualityLevel)
        self.StatusInfo = []     # list of string (uri)
        self.Complexity = None   # string
        self.Endpoint = []       # list of string (uri)
        self.Share = []          # list of string (LocalID)
        self.Contact = []        # list of string (uri)
        self.Location = None     # string (uri)
        self.Service = []        # list of string (uri)

        # ComputingService
        self.TotalJobs = None          # integer
        self.RunningJobs = None        # integer
        self.WaitingJobs = None        # integer
        self.StagingJobs = None        # integer
        self.SuspendedJobs = None      # integer
        self.PreLRMSWaitingJobs = None # integer
        self.ComputingEndpoint = []   # list of string (uri)
        #self.computingEndpoint = []    # list of ComputingEndpoint
        self.ComputingShare = []      # list of string (uri)
        self.ComputingManager = None  # string (uri)
        #self.computingManager = None   # ComputingManager (set by child class)
        self.StorageService = []       # list of string (uri)

    def _setBody(self, body):
        logger.info("ComputingService._setBody should parse the XML...")

    def _getBody(self):
        return self._toXml()

    def _toXml(self, indent=""):
        mstr = indent+"<ComputingService"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                  Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name != None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"++"'>"+self.Extension[key]+"</Extension>\n"

        # Service
        for capability in self.Capability:
            mstr = mstr+indent+"  <Capability>"+capability+"</Capability>\n"
        if self.Type != None:
            mstr = mstr+indent+"  <Type>"+self.Type+"</Type>\n"
        if self.QualityLevel != None:
            mstr = mstr+indent+"  <QualityLevel>"+self.QualityLevel+"</QualityLevel>\n"
        for status in self.StatusInfo:
            mstr = mstr+indent+"  <StatusInfo>"+status+"</StatusInfo>\n"
        if self.Complexity != None:
            mstr = mstr+indent+"  <Complexity>"+self.Complexity+"</Complexity>\n"
        for endpoint in self.Endpoint:
            mstr = mstr+indent+"  <Endpoint>"+endpoint+"</Endpoint>\n"
        for share in self.Share:
            mstr = mstr+indent+"  <Share>"+Share+"</Share>\n"
        for contact in self.Contact:
            mstr = mstr+indent+"  <Contact>"+contact+"</Contact>\n"
        if self.Location != None:
            mstr = mstr+indent+"  <Location>"+self.Location+"</Location>\n"
        for service in self.Service:
            mstr = mstr+indent+"  <Service>"+Service+"</Service>\n"

        # ComputingService
        if self.TotalJobs != None:
            mstr = mstr+indent+"  <TotalJobs>"+str(self.TotalJobs)+"</TotalJobs>\n"
        if self.RunningJobs != None:
            mstr = mstr+indent+"  <RunningJobs>"+str(self.RunningJobs)+"</RunningJobs>\n"
        if self.WaitingJobs != None:
            mstr = mstr+indent+"  <WaitingJobs>"+str(self.WaitingJobs)+"</WaitingJobs>\n"
        if self.StagingJobs != None:
            mstr = mstr+indent+"  <StagingJobs>"+str(self.StagingJobs)+"</StagingJobs>\n"
        if self.SuspendedJobs != None:
            mstr = mstr+indent+"  <SuspendedJobs>"+str(self.SuspendedJobs)+"</SuspendedJobs>\n"
        if self.PreLRMSWaitingJobs != None:
            mstr = mstr+indent+"  <PreLRMSWaitingJobs>"+str(self.PreLRMSWaitingJobs)+"</PreLRMSWaitingJobs>\n"
        for id in self.ComputingEndpoint:
            mstr = mstr+indent+"  <ComputingEndpoint>"+id+"</ComputingEndpoint>\n"
        for id in self.ComputingShare:
            mstr = mstr+indent+"  <ComputingShare>"+id+"</ComputingShare>\n"
        if self.ComputingManager != None:
            mstr = mstr+indent+"  <ComputingManager>"+self.ComputingManager+"</ComputingManager>\n"

        mstr = mstr+indent+"</ComputingService>\n"
        return mstr
