
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
import time
import stat
import sys

from ipf.error import StepError

#######################################################################################################################

logger = logging.getLogger(__name__)

#######################################################################################################################

class LogFileWatcher(object):
    def __init__(self, callback, path, posdb_path=None):
        self.callback = callback
        self.path = path
        self.keep_running = True
        self.pos_db = PositionDB(posdb_path)

    def run(self):
        file = LogFile(self.path,self.callback,self.pos_db)
        file.open()
        while self.keep_running:
            try:
                file.handle()
            except IOError:
                # try to reopen in case of stale NFS file handle or similar
                file.reopen()
                file.handle()
            time.sleep(1)
        file.close()

    def stop(self):
        self.keep_running = False
        
#######################################################################################################################

class LogDirectoryWatcher(object):
    """Discovers new lines in log files and sends them to the callback."""

    def __init__(self, callback, dir, posdb_path=None):
        if not os.path.exists(dir):
            raise StepError("%s doesn't exist",dir)
        if not os.path.isdir(dir):
            raise StepError("%s isn't a directory",dir)

        self.callback = callback
        self.dir = dir
        self.pos_db = PositionDB(posdb_path)
        self.files = {}
        self.last_update = -1

        logger.info("created watcher for directory %s",dir)
        
    def run(self):
        while True:
            self._updateFiles()
            for file in self.files.values():
                try:
                    file.handle()
                except IOError:
                    # try to reopen in case of stale NFS file handle or similar
                    file.reopen()
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
            if not os.path.isfile(path):  # only regular files
                continue
            if os.path.islink(path):      # but not soft links
                continue
            cur_files.append(LogFile(path,self.callback,self.pos_db))
        return cur_files

    def _handleExistingFile(self, file):
        logger.debug("existing file %s",file.path)
        if file.path != self.files[file.id].path:  # file has been rotated
            logger.info("log file %s rotated to %s",self.files[file.id].path,file.path)
            self.files[file.id].path = file.path
        file.closeIfNeeded()

    def _handleNewFile(self, file):
        logger.info("new file %s %s",file.id,file.path)
        file.openIfNeeded()
        self.files[file.id] = file

    def _handleDeletedFiles(self, cur_files):
        cur_file_ids = set(map(lambda file: file.id,cur_files))
        for id in filter(lambda id: id not in cur_file_ids,self.files.keys()):
            if self.files[id].file is not None:
                self.files[id].file.close()
            del self.files[id]
        for id in self.pos_db.ids():
            if id not in self.files:
                self.pos_db.remove(id)

#######################################################################################################################

class LogFile(object):
    def __init__(self, path, callback, pos_db = None):
        self.path = path
        st = os.stat(path)
        self.id = self._getId(st)
        self.callback = callback
        self.file = None
        if pos_db is None:
            self.pos_db = PositionDB()
        else:
            self.pos_db = pos_db
            
    def _getId(self, st):
        return "%s-%d" % (st.st_dev, st.st_ino)

    def openIfNeeded(self):
        if self._shouldOpen():
            self.open()

    def _shouldOpen(self):
        if self.file is not None:
            return False
        st = os.stat(self.path)
        if st.st_mtime > time.time() - 15*60:
            return True
        return False

    def _seek(self):
        position = self.pos_db.get(self.id)
        if position is not None:
            self.file.seek(position)
        else:
            self.file.seek(0,os.SEEK_END)
            self._savePosition()

    def _savePosition(self):
        return self.pos_db.set(self.id,self.file.tell())

    def _forgetPosition(self):
        self.pos_db.remove(self.id)

    def open(self):
        logger.info("opening file %s (%s)",self.id,self.path)
        if self.file is not None:
            logger.warn("attempting to open already open file %s",self.path)
        self.file = open(self.path,"r")
        self._seek()

    def reopen(self):
        logger.info("reopening file %s (%s)",self.id,self.path)
        self.file = open(self.path,"r")
        self._seek()

    def closeIfNeeded(self):
        if self._shouldClose():
            self.close()
            #self._forgetPosition()
            
    def _shouldClose(self):
        if self.file is None:
            return False
        st = os.stat(self.path)
        if st.st_mtime < time.time() - 15*60:
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
        self._seek()
        while line:
            line = self.file.readline()
            if not line.endswith("\n"):
                self.callback(self.path,line)
                self._savePosition()
            else
                break
            

#######################################################################################################################

class PositionDB(object):
    def __init__(self, path=None):
        self.position = {}
        self.path = path
        self._read()

    def set(self, id, position):
        if id not in self.position or position != self.position[id]:
            self.position[id] = position
            self._write()

    def get(self, id):
        return self.position.get(id,None)

    def remove(self, id):
        del self.position[id]
        self._write()

    def ids(self):
        return self.position.keys()

    def _read(self):
        if self.path is None:
            return
        self.position = {}
        if not os.path.exists(self.path):
            return
        try:
            file = open(self.path,"r")
            for line in file:
                (id,pos_str) = line.split()
                self.position[id] = int(pos_str)
            file.close()
        except IOError, e:
            logger.error("failed to read position database %s: %s" % (self.path,e))

    def _write(self):
        if self.path is None:
            return
        try:
            file = open(self.path,"w")
            for key in self.position:
                file.write("%s %d\n" % (key,self.position[key]))
            file.close()
        except IOError, e:
            logger.error("failed to write position database %s: %s" % (self.path,e))

#######################################################################################################################

# testing

def echo(path, message):
    print("%s: %s" % (path,message[:-1]))

def doNothing(path, message):
    pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: log.py <log directory> [position file]")
        sys.exit(1)

    import logging.config
    from ipf.paths import IPF_ETC_PATH

    if len(sys.argv) >= 3:
        watcher = LogDirectoryWatcher(echo,sys.argv[1],sys.argv[2])
    else:
        watcher = LogDirectoryWatcher(echo,sys.argv[1])
    watcher.run()
