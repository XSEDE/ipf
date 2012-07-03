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

from ipf.error import StepError

from glue2.computing_share import *

#######################################################################################################################

class LsfComputingSharesStep(ComputingSharesStep):

    def __init__(self, params):
        ComputingSharesStep.__init__(self,params)

        self.name = "glue2/lsf/computing_shares"
        self.accepts_params["bqueues"] = "the path to the LSF bqueues program (default 'bqueues')"

    def _run(self):
        self.info("running")

        bqueues = self.params.get("bqueues","bqueues")

        cmd = bqueues + " -l"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("bqueues failed: "+output+"\n")

        queues = []
        queueStrings = output.split("------------------------------------------------------------------------------")
        for queueString in queueStrings:
            queue = self._getQueue(queueString)
            if includeQueue(self.config,queue.Name):
                queues.append(queue)
        return queues

    def _getQueue(self, queueString):
        queue = ComputingShare()

        lineNumber = 0
        lines = queueString.split("\n")

        queueName = None
        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("QUEUE:"):
                queueName = lines[lineNum][7:]
                lineNumber = lineNum + 1
                break
        if queueName == None:
            raise StepError("Error: didn't find queue name in output: "+queueString)

        ComputingShare.__init__(self,sensor)

        queue.Name = queueName
        queue.MappingQueue = queue.Name

        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("  -- "):
                queue.Description = lines[lineNum][5:]
                lineNumber = lineNum + 1
                break

        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("PRIO NICE"):
                (prio,nice,status,max,jlu,jlp,jlh,njobs,pend,run,ssusp,ususp,rsv) = lines[lineNum+1].split()
                queue.Extension["Priority"] = int(prio)
                lineNumber = lineNum + 2
                break
        
        defaultLimitsStart = -1
        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("DEFAULT LIMITS:"):
                defaultLimitsStart = lineNum + 1
                lineNumber = lineNum + 1
                break

        maxLimitsStart = -1
        for lineNum in range(lineNumber,len(lines)):
            if lines[lineNum].startswith("MAXIMUM LIMITS:"):
                maxLimitsStart = lineNum + 1
                lineNumber = lineNum + 1
                break

        queue.DefaultWallTime = queue.getRunLimit(lines,defaultLimitsStart,maxLimitsStart)

        queue.MaxWallTime = queue.getRunLimit(lines,maxLimitsStart,len(lines))
        (minSlots,defaultSlots,queue.MaxSlotsPerJob) = queue.getCpuLimits(lines,maxLimitsStart,len(lines))
        if minSlots != None:
            queue.Extension["MinSlotsPerJob"] = str(minSlots)
        if defaultSlots != None:
            queue.Extension["DefaultSlotsPerJob"] = str(defaultSlots)

        # this info is a little more sensitive and perhaps shouldn't be made public
        # uncomment the return below to not publish it
        #return
        
        authorizedUsers = []
        authorizedGroups = []
        for lineNum in range(lineNumber, len(lines)):
            if lines[lineNum].startswith("USERS:"):
                usersGroups = lines[lineNum][7:].split()
                for userOrGroup in usersGroups:
                    if userOrGroup.endswith("/"):
                        authorizedGroups.append(userOrGroup[:len(userOrGroup)-1])
                    else:
                        if userOrGroup == "all": # LSF has a special token 'all'
                            authorizedUsers.append("*")
                        else:
                            authorizedUsers.append(userOrGroup)
                lineNumber = lineNum + 1
                break
        if len(authorizedUsers) > 0:
            authUserStr = None
            for user in authorizedUsers:
                if authUserStr == None:
                    authUserStr = user
                else:
                    authUserStr = authUserStr + " " + user
            # lets not include this right now in case of privacy concerns
            #queue.Extension["AuthorizedUsers"] = authUserStr

        if len(authorizedGroups) > 0:
            authGroupStr = None
            for group in authorizedGroups:
                if authGroupStr == None:
                    authGroupStr = group
                else:
                    authGroupStr = authGroupStr + " " + group
            # lets not include this right now in case of privacy concerns
            #queue.Extension["AuthorizedGroups"] = authGroupStr

    def getRunLimit(self, lines, startIndex, endIndex):
        for lineNum in range(startIndex,endIndex):
            if lines[lineNum].startswith(" RUNLIMIT"):
                toks = lines[lineNum+1].split()
                if len(toks) < 2:
                    self.warn("failed to parse run limit")
                    return None
                if toks[1] != "min":
                    self.warn("don't understand time unit '" + toks[1] + "'")
                    return None
                return float(toks[0])*60
        return None


    def getCpuLimits(self, lines, startIndex, endIndex):
        # returns (min, default, max)
        for lineNum in range(startIndex,endIndex):
            if lines[lineNum].startswith(" PROCLIMIT"):
                toks = lines[lineNum+1].split()
                if len(toks) == 1:
                    return (None, None, int(toks[0]))
                if len(toks) == 2:
                    return (int(toks[0]), None, int(toks[1]))
                if len(toks) == 3:
                    return (int(toks[0]), int(toks[1]), int(toks[2]))
                return (None,None,None)
        return (None,None,None)

#######################################################################################################################
