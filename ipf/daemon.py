
###############################################################################
#   Copyright 2012-2014 The University of Texas at Austin                     #
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

from ipf.paths import IPF_VAR_PATH

logger = logging.getLogger(__name__)

##############################################################################################################

class OneProcessOnly:
    def __init__(self, pidfile):
        self.pid_file_name = pidfile

    def start(self):
        if self._isRunning():
            logger.error("process is already running at %s" % self.pid_file_name)
            return
        self._writePid()
        self.run()
        self._removePid()

    def _isRunning(self):
        if self.pid_file_name is None:
            # no way to tell
            False
        try:
            pid_file = open(self.pid_file_name,"r")
            pid_str = pid_file.readline()
            pid_file.close()
            logger.debug("pid is "+pid_str)
        except IOError:
            logger.debug("no pid file")
            return False

        if (pid_str != None) and os.path.exists("/proc/"+pid_str):
            # could check /proc/pid_str/cmdline and ...
            logger.debug("found running daemon")
            return True
        logger.debug("no running daemon")
        return False

    def _writePid(self):
        if self.pid_file_name is None:
            return
        # save process id in the .pid file
        pid_file = open(self.pid_file_name,"w")
        pid_file.write(str(os.getpid()))
        pid_file.close()

    def _removePid(self):
        if self.pid_file_name is None:
            return
        try:
            os.remove(self.pid_file_name)
        except IOError:
            logger.warning("failed to remove pid file %s" % self.pid_file_name)

    def _redirect(self, stdin_file_name, stdout_file_name, stderr_file_name):
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(stdin_file_name, 'r')
        so = open(stdout_file_name, 'a+')
        se = open(stderr_file_name, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def run(self):
        raise NotImplementedError()

##############################################################################################################

class OneProcessWithRedirect(OneProcessOnly):
    def __init__(self, pidfile=None, stdin="/dev/null", stdout="/dev/null", stderr="/dev/null"):
        OneProcessOnly.__init__(self,pidfile)
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def start(self):
        if self._isRunning():
            logger.error("process is already running at %s" % self.pid_file_name)
            return
        self._writePid()
        self._redirect(self.stdin,self.stdout,self.stderr)
        self.run()
        self._removePid()
 
    def run(self):
        raise NotImplementedError()

##############################################################################################################

class Daemon(OneProcessOnly):
    def __init__(self, pidfile=None, stdin="/dev/null", stdout="/dev/null", stderr="/dev/null"):
        OneProcessOnly.__init__(self,pidfile)
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def start(self):
        if not self._isRunning():
            self._daemonize()
            self._writePid()
            self.run()

    def _daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
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
        except OSError as e:
            logger.error("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        self._redirect(self.stdin,self.stdout,self.stderr)
 
    def run(self):
        raise NotImplementedError()

##############################################################################################################

class TestDaemon(Daemon):
    def __init__(self):
        pidFile = os.path.join(IPF_VAR_PATH,"daemon_test.pid")
        stdoutFile = os.path.join(IPF_VAR_PATH,"daemon_test.stdout")
        stderrFile = os.path.join(IPF_VAR_PATH,"daemon_test.stderr")
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
