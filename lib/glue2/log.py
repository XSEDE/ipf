
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
import time
import stat
import sys

from ipf.error import StepError

#######################################################################################################################

# load config file while testing
import logging.config
ipfHome = os.environ.get("IPF_HOME")
if ipfHome == None:
    raise IpfError("IPF_HOME environment variable not set")
logging.config.fileConfig(os.path.join(ipfHome,"etc","logging.conf"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#######################################################################################################################

class LogFileWatcher(object):
    def __init__(self, callback, path):
        self.callback = callback
        self.path = path
        self.keep_running = True

    def run(self):
        file = LogFile(self.path,self.callback)
        file.open()
        while self.keep_running:
            file.handle()
            time.sleep(1)
        file.close()

    def stop(self):
        self.keep_running = False
        
#######################################################################################################################

class LogDirectoryWatcher(object):
    """Discovers new lines in log files and sends them to the callback."""

    def __init__(self, callback, dir):
        if not os.path.exists(dir):
            raise StepError("%s doesn't exist",dir)
        if not os.path.isdir(dir):
            raise StepError("%s isn't a directory",dir)

        self.callback = callback
        self.dir = dir
        self.files = {}
        self.last_update = -1

        logger.info("created watcher for directory %s",dir)
        
    def run(self):
        while True:
            self._updateFiles()
            for file in self.files.values():
                file.handle()
            time.sleep(1)
                        
    def _updateFiles(self):
        cur_time = time.time()
        if cur_time - self.last_update < 60:  # update files once a minute
            return
        logger.debug("updating files")
        cur_files = self._getCurrentFiles()
        for file in cur_files:
            if file.id in self.files:
                self._handleExistingFile(file)
            else:
                self._handleNewFile(file)
        self._handleDeletedFiles(cur_files)
        self.last_update = cur_time

    def _getCurrentFiles(self):
        cur_files = []
        for file_name in os.listdir(self.dir):
            path = os.path.join(self.dir,file_name)
            st = os.stat(path)
            if not stat.S_ISREG(st.st_mode):
                continue
            cur_files.append(LogFile(path,self.callback,st))
        return cur_files

    def _handleExistingFile(self, file):
        logger.debug("existing file %s",file.path)
        if file.path != self.files[file.id].path:  # file has been rotated
            logger.info("log file %s rotated to %s",self.files[file.id].path,file.path)
            file.open(self.files[file.id].where)
            self.files[file.id].close()
            self.files[file.id] = file
        else:
            file.closeIfNeeded()

    def _handleNewFile(self, file):
        logger.info("new file %s %s",file.id,file.path)
        if self.last_update > 0:  # a new file
            file.open(0)
        else:                     # starting up
            file.openIfNeeded()
        self.files[file.id] = file

    def _handleDeletedFiles(self, cur_files):
        if len(self.files) <= len(cur_files):
            return
        cur_file_ids = set()
        for file in cur_files:
            cur_file_ids.add(file.id)
        to_delete = []
        for id in self.files:
            if id in cur_file_ids:
                continue
            if self.files[id].file != None:
                self.files[id].file.close()
            to_delete.append(id)
        for id in to_delete:
            del self.files[id]

#######################################################################################################################

class LogFile(object):
    def __init__(self, path, callback, st=None):
        self.path = path
        self.id = self._getId(st)
        if st is None:
            st = os.stat(path)
        self.mod_time = st.st_mtime
        self.callback = callback
        self.file = None
        self.where = None
            
    def _getId(self, st):
        return "%s-%d" % (st.st_dev, st.st_ino)

    def openIfNeeded(self):
        if self._shouldOpen():
            self.open()

    def _shouldOpen(self):
        if self.file is not None:
            return False
        if self.mod_time > time.time() - 15*60:
            return True
        return False

    def open(self, where=None):
        logger.info("opening file %s (%s)",self.id,self.path)
        if self.file is not None:
            logger.warn("attempting to open already open file %s",self.path)
        self.file = open(self.path,"r")
        if where is None:
            self.file.seek(0,os.SEEK_END)
            self.where = self.file.tell()
        else:
            self.where = where

    def closeIfNeeded(self):
        if self._shouldClose():
            self.close()
            
    def _shouldClose(self):
        if self.file is None:
            return False
        if self.mod_time < time.time() - 15*60:
            return True
        return False

    def close(self):
        logger.info("closing file %s (%s)",self.id,self.path)
        if self.file is None:
            logger.warn("attempting to close already closed file %s",self.path)
            return
        self.file.close()
        self.file = None

    def handle(self):
        if self.file is None:
            return
        logger.debug("checking log file %s",self.path)
        line = "junk"
        self.file.seek(self.where)
        while line:
            line = self.file.readline()
            if line:
                self.callback(self.path,line)
        self.where = self.file.tell()

#######################################################################################################################

def echo(path, message):
    print("%s: %s" % (path,message))

def doNothing(path, message):
    pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: log.py <log directory>")
        sys.exit(1)
    watcher = LogDirectoryWatcher(doNothing,sys.argv[1])
    watcher.run()
