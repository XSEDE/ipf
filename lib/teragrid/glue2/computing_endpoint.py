
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
import logging
import os
import socket
import sys
import time
import ConfigParser

from ipf.document import Document
from teragrid.tgagent import TeraGridAgent
from teragrid.xmlhelper import *

logger = logging.getLogger("ComputingEndpointsAgent")

##############################################################################################################

class ComputingEndpointsAgent(TeraGridAgent):
    def __init__(self, args={}):
        TeraGridAgent.__init__(self,args)
        self.description = "This agent provides documents in the GLUE 2 ComputingEndpoint schema. This could be something like LSF or SGE or it could be something like GRAM."
        self.default_timeout = 15

##############################################################################################################

class ComputingEndpoint(Document):
    def __init__(self):
        Document.__init__(self)
        self.type = "teragrid.glue2.ComputingEndpoint"
        self.content_type = "text/xml"

        # Entity
        self.ID = None      # string (uri)
        self.Name = None    # string
        self.OtherInfo = [] # list of string
        self.Extension = {} # (key,value) strings

        # Endpoint
        self.URL = None                   # string (uri)
        self.Capability = []              # list of string (Capability)
        self.Technology = None            # string (EndpointTechnology)
        self.InterfaceName = None         # string (InterfaceName)
        self.InterfaceVersion = None      # string
        self.InterfaceExtension = []      # list of string (uri)
        self.WSDL = []                    # list of string (uri)
        self.SupportedProfile = []        # list of string (uri)
        self.Semantics = []               # list of string (uri)
        self.Implementor = None           # string
        self.ImplementationName = None    # string
        self.ImplementationVersion = None # string
        self.QualityLevel = None          # string (QualityLevel)
        self.HealthState = None           # string (EndpointHealthState)
        self.HealthStateInfo = None       # string
        self.ServingState = None          # string (ServingState)
        self.StartTime = None             # datetime
        self.IssuerCA = None              # string (DN)
        self.TrustedCA = []               # list of string (DN)
        self.DowntimeAnnounce = None      # datetime
        self.DowntimeStart = None         # datetime
        self.DowntimeEnd = None           # datetime
        self.DowntimeInfo = None          # string

        # ComputingEndpoint
        self.Staging = None            # string (Staging)
        self.JobDescription = []       # list of string (JobDescription)
        self.TotalJobs = None          # integer
        self.RunningJobs = None        # integer
        self.WaitingJobs = None        # integer
        self.StagingJobs = None        # integer
        self.SuspendedJobs = None      # integer
        self.PreLRMSWaitingJobs = None # integer
        self.ComputingService = None   # string (uri)
        self.ComputingShare = []       # list of string (uri)
        self.ComputingActivity = []    # list of string (uri)

        # required attributes that may be forgotten
        self.HealthState = "unknown"
        self.ServingState = "production"

    def _setBody(self, body):
        logger.info("ComputingEndpoint._setBody should parse the XML...")

    def _getBody(self):
        return self._toXml()
    
    def _toXml(self, indent=""):
        mstr = indent+"<ComputingEndpoint"

        # Entity
        curTime = time.time()
        mstr = mstr+" CreationTime='"+epochToXmlDateTime(curTime)+"'\n"
        mstr = mstr+indent+"                   Validity='300'>\n"
        mstr = mstr+indent+"  <ID>"+self.ID+"</ID>\n"
        if self.Name != None:
            mstr = mstr+indent+"  <Name>"+self.Name+"</Name>\n"
        for info in self.OtherInfo:
            mstr = mstr+indent+"  <OtherInfo>"+info+"</OtherInfo>\n"
        for key in self.Extension.keys():
            mstr = mstr+indent+"  <Extension Key='"++"'>"+self.Extension[key]+"</Extension>\n"

        # Endpoint
        if self.URL != None:
            mstr = mstr+indent+"  <URL>"+self.URL+"</URL>\n"
        for capability in self.Capability:
            mstr = mstr+indent+"  <Capability>"+capability+"</Capability>\n"
        if self.Technology != None:
            mstr = mstr+indent+"  <Technology>"+self.Technology+"</Technology>\n"
        if self.InterfaceName != None:
            mstr = mstr+indent+"  <InterfaceName>"+self.InterfaceName+"</InterfaceName>\n"
        if self.InterfaceVersion != None:
            mstr = mstr+indent+"  <InterfaceVersion>"+self.InterfaceVersion+"</InterfaceVersion>\n"
        for extension in self.InterfaceExtension:
            mstr = mstr+indent+"  <InterfaceExtension>"+extension+"</InterfaceExtension>\n"
        for wsdl in self.WSDL:
            mstr = mstr+indent+"  <WSDL>"+wsdl+"</WSDL>\n"
        for profile in self.SupportedProfile:
            mstr = mstr+indent+"  <SupportedProfile>"+profile+"</SupportedProfile>\n"
        for semantics in self.Semantics:
            mstr = mstr+indent+"  <Semantics>"+semantics+"</Semantics>\n"
        if self.Implementor != None:
            mstr = mstr+indent+"  <Implementor>"+self.Implementor+"</Implementor>\n"
        if self.ImplementationName != None:
            mstr = mstr+indent+"  <ImplementationName>"+self.ImplementationName+"</ImplementationName>\n"
        if self.ImplementationVersion != None:
            mstr = mstr+indent+"  <ImplementationVersion>"+self.ImplementationVersion+"</ImplementationVersion>\n"
        if self.QualityLevel != None:
            mstr = mstr+indent+"  <QualityLevel>"+self.QualityLevel+"</QualityLevel>\n"
        if self.HealthState != None:
            mstr = mstr+indent+"  <HealthState>"+self.HealthState+"</HealthState>\n"
        if self.HealthStateInfo != None:
            mstr = mstr+indent+"  <HealthStateInfo>"+self.HealthStateInfo+"</HealthStateInfo>\n" # ?
        if self.ServingState != None:
            mstr = mstr+indent+"  <ServingState>"+self.ServingState+"</ServingState>\n"
        if self.StartTime != None:
            mstr = mstr+indent+"  <StartTime>"+self.StartTime+"</StartTime>\n"
        if self.IssuerCA != None:
            mstr = mstr+indent+"  <IssuerCA>"+self.IssuerCA+"</IssuerCA>\n"
        for trustedCA in self.TrustedCA:
            mstr = mstr+indent+"  <TrustedCA>"+trustedCA+"</TrustedCA>\n"
        if self.DowntimeAnnounce != None:
            mstr = mstr+indent+"  <DowntimeAnnounce>"+self.DowntimeAnnounce+"</DowntimeAnnounce>\n"
        if self.DowntimeStart != None:
            mstr = mstr+indent+"  <DowntimeStart>"+self.DowntimeStart+"</DowntimeStart>\n"
        if self.DowntimeEnd != None:
            mstr = mstr+indent+"  <DowntimeEnd>"+self.DowntimeEnd+"</DowntimeEnd>\n"
        if self.DowntimeInfo != None:
            mstr = mstr+indent+"  <DowntimeInfo>"+self.DowntimeInfo+"</DowntimeInfo>\n"

        # ComputingEndpoint
        if self.Staging != None:
            mstr = mstr+indent+"  <Staging>"+self.Staging+"</Staging>\n"
        for description in self.JobDescription:
            mstr = mstr+indent+"  <JobDescription>"+description+"</JobDescription>\n"
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
        if self.ComputingService != None:
            mstr = mstr+indent+"  <ComputingService>"+self.ComputingService+"</ComputingService>\n"
        for share in  self.ComputingShare:
            mstr = mstr+indent+"  <ComputingShare>"+share+"</ComputingShare>\n"
        for activity in  self.ComputingActivity:
            mstr = mstr+indent+"  <ComputingActivity>"+activity+"</ComputingActivity>\n"
        mstr = mstr+indent+"</ComputingEndpoint>\n"

        return mstr
