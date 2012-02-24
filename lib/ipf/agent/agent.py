
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
import threading
import traceback

import ConfigParser

from ipf.error import *

home_dir = os.environ.get("GLUE2_HOME")
if home_dir == None:
    print "GLUE2_HOME environment variable not set"
    sys.exit(1)

logger = logging.getLogger()
handler = logging.FileHandler(os.path.join(home_dir,"var","agent.log"))
formatter = logging.Formatter("%(asctime)s %(levelname)s - %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARN)

##############################################################################################################

class Agent(object):
    def __init__(self, args={}):
        self.name = None
        self.description = None
        self.default_timeout = None
        self._doc_class = {}      # child classes should add to this
        self.args = args
        self._loadConfig()
        self._addToConfig(args)

        self.host_name = None
        
    def _loadConfig(self):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(home_dir+"/etc/agent.cfg")

    def _addToConfig(self, args):
        for name in args.keys():
            index = name.find(".")
            if index < 0:
                section = "default"
                option = name
            else:
                section = name[:index]
                option = name[index+1:]
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section,option,args[name])

    def usage(cls):
        # name?
        # valid paths (input and output)?
        # valid content types (input and output)?
        # valid schemas?
        print("usage: <command> [argname=argvalue]* where command is one of:\n" +
              "    description: output a human-readable description of this agent to stdout\n" +
              "    arguments: output a list of valid arguments and descriptions to stdout\n" +
              "    run: run the agent with input docs on stdin and output docs sent to stdout\n")
    usage = classmethod(usage)

    def _getHostName(self):
        if self.host_name == None:
            self._setHostName()
        return self.host_name

    def _setHostName(self):
        try:
            self.host_name = self.config.get("default","hostname")
            return
        except ConfigParser.Error:
            pass
        self.host_name = socket.gethostname()

    def createFromCommandLine(cls):
        if len(sys.argv) < 2:
            cls.usage()
            sys.exit(1)

        if sys.argv[1] == "description":
            print(self.description)
            sys.exit(0)
        elif sys.argv[1] == "arguments":
            print("can't output arguments yet")
            sys.exit(0)
        elif sys.argv[1] == "run":
            args = {}
            for index in range(2,len(sys.argv)):
                (name,value) = sys.argv[index].split("=")
                args[name] = value
        return cls(args)
    createFromCommandLine = classmethod(createFromCommandLine)

    def runStdinStdout(self):
        try:
            return self._runFDs(sys.stdin,sys.stdout)
        except:
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    def _runFDs(self, fd_in, fd_out):
        docs_in = []
        if fd_in != None:
            doc = self._readDoc(fd_in)
            while doc != None:
                docs_in.append(doc)
                doc = self._readDoc(fd_in)

        docs_out = self.run(docs_in)

        if fd_out != None and docs_out != None:
            for doc in docs_out:
                #print(doc.body)
                doc.write(fd_out)

    def _readDoc(self, fd):
        line = fd.readline()
        if line == "":
            return None

        #(put,path) = line.split()
        id = line
        if not id in self._doc_class:
            raise AgentError("agent "+self.name+" doesn't recognize doc "+id)

        doc = self._doc_class[id]()
        doc.read(id)
        return doc

    def runWithTimeOut(self, docs_in=[]):
        """Run the agent and return with output docs."""
        # run with a timeout
        thread = AgentThread(self,docs_in)
        thread.start()
        thread.join(self._getTimeOut())
        if self.error != None:
            raise self.error
        if not self.complete:
            raise AgentError("agent "+self.name+" did not complete task within "+str(self._getTimeOut())+" seconds")
        return thread.docs_out

    def _getTimeOut(self):
        if config.get(self.name,"timeout") != "":
            return int(config.get(self.name,"timeout"))
        if config.get("default","timeout") != "":
            return int(config.get("default","timeout"))
        if self.default_timeout != None:
            return self.default_timeout
        return 15

    def run(self, docs_in=[]):
        """Run the agent and return a list of output docs."""
        print "Agent.run not overridden"
        sys.exit(1)

class AgentThread(threading.Thread):
    def __init__(self, agent, docs_in=None):
        self.agent = agent
        self.docs_in = docs_in
        self.complete = False
        self.docs_out = None
        self.error = None

    def run(self):
        try:
            self.docs_out = self.agent.run(docs_in)
        except Exception, error:
            self.error = error
        self.complete = True
