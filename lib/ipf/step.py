
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
import urlparse

import ConfigParser

ipfHome = os.environ.get("IPF_HOME")
if ipfHome == None:
    print "IPF_HOME environment variable not set"
    sys.exit(1)

logger = logging.getLogger()
handler = logging.FileHandler(os.path.join(ipfHome,"var","step.log"))
formatter = logging.Formatter("%(asctime)s %(levelname)s - %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARN)

##############################################################################################################

class Step:
    def __init__(self):
        self.name = None
        self.description = None
        #self.inputUri = []
        #self.outputUri = []
        #self.inputContentType = []
        #self.outputContentType = []
        self.defaultTimeOut = None

        self.config = ConfigParser.ConfigParser()
        self.config.read(ipfHome+"/etc/ipf.config")

    def usage(self):
        return "usage: \"<sensor> <command>\" where command is one of:\n" + \
            "    name: name of the sensor\n" + \
            "    description: user-readable description of the step\n" + \
            "    input_uri: comma-separated list of the uris this step can accept\n" + \
            "    output_uri: comma-separated list of the uris this step can produce\n" + \
            "    input_content_type: comma-separated list of the content types this step can accept\n" + \
            "    output_content_type: comma-separated list of the content types this step can produce\n" + \
            "    default_timeout: suggested duration to wait for this step to complete (xsd:duration)\n" + \
            "    run: perform a step\n"

    def handle(self):
        if sys.argv[1] == "name":
            print(self.name)
            sys.exit(0)
        if sys.argv[1] == "description":
            print(self.description)
            sys.exit(0)
        #if sys.argv[1] == "input_uri":
        #    for i in range(0,len(self.input_uri)):
        #        if i > 0:
        #            print(",")
        #        print(self.input_uri[i])
        #    sys.exit(0)
        #if sys.argv[1] == "output_uri":
        #    for i in range(0,len(self.output_uri)):
        #        if i > 0:
        #            print(",")
        #        print(self.output_uri[i])
        #    sys.exit(0)
        #if sys.argv[1] == "input_content_type":
        #    for i in range(0,len(self.input_content_type)):
        #        if i > 0:
        #            print(",")
        #        print(self.input_content_type[i])
        #    sys.exit(0)
        #if sys.argv[1] == "output_content_type":
        #    for i in range(0,len(self.output_content_type)):
        #        if i > 0:
        #            print(",")
        #        print(self.output_content_type[i])
        #    sys.exit(0)
        if sys.argv[1] == "default_timeout":
            print self.default_timeout
            sys.exit(0)
        if sys.argv[1] == "run":
            self.run()
        print "unknown command: '"+sys.argv[1]+"'"
        print self.usage()
        sys.exit(1)

    def _getHostName(self):
        hostName = self.config.get("default","hostname")
        if hostName != None:
            return hostName
        return socket.gethostname()

    def run(self):
        """Run the step."""
        print "Step.run not overridden"
        sys.exit(1)
