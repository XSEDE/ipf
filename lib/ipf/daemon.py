
###############################################################################
#   Copyright 2012 The University of Texas at Austin                          #
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

import logging
import os
import sys
import time

from ipf.home import IPF_HOME

logger = logging.getLogger(__name__)

##############################################################################################################

class Daemon:
    def __init__(self, pidfile=None, stdin="/dev/null", stdout="/dev/null", stderr="/dev/null"):
        self.pidFileName = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def start(self):
        if self.shouldStart():
            self.daemonize()
            self.writePid()
            self.run()

    def shouldStart(self):
        try:
            pidFile = open(self.pidFileName,"r")
            pidStr = pidFile.readline()
            pidFile.close()
            logger.debug("pid is "+pidStr)
        except IOError:
            logger.debug("no pid file")
            return True

        if (pidStr != None) and os.path.exists("/proc/"+pidStr):
            logger.debug("found running daemon")
            return False
        logger.debug("no running daemon")
        return True

    def writePid(self):
        if self.pidFileName == None:
            return
        # save process id in the .pid file
        pidFile = open(self.pidFileName,"w")
        pidFile.write(str(os.getpid()))
        pidFile.close()

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            logger.error("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            logger.error("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
 
    def run(self):
        raise NotImplementedError()

##############################################################################################################

class TestDaemon(Daemon):
    def __init__(self):
        pidFile = os.path.join(IPF_HOME,"var","daemon_test.pid")
        stdoutFile = os.path.join(IPF_HOME,"var","daemon_test.stdout")
        stderrFile = os.path.join(IPF_HOME,"var","daemon_test.stderr")
        Daemon.__init__(self,pidfile=pidFile,stdout=stdoutFile,stderr=stderrFile)

    def run(self):
        for i in range(0,10):
            print("printing to stdout")
        time.sleep(10)
        for i in range(0,10):
            sys.stdout.write("writing to stdout\n")
        time.sleep(10)
        for i in range(0,10):
            sys.stderr.write("writing to stderr\n")
        time.sleep(10)
        print("test done")
        
##############################################################################################################

if __name__ == "__main__":
    daemon = TestDaemon()
    daemon.start()
