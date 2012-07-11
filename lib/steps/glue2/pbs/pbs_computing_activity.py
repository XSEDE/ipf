
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

import commands
import datetime
import os
import re

from ipf.error import StepError
from glue2.log import LogDirectoryWatcher

from glue2.computing_activity import *

#######################################################################################################################

class PbsComputingActivitiesStep(ComputingActivitiesStep):

    def __init__(self, params):
        ComputingActivitiesStep.__init__(self,params)

        self.name = "glue2/pbs/computing_activities"
        self.accepts_params["qstat"] = "the path to the PBS qstat program (default 'qstat')"

    def _run(self):
        qstat = self.params.get("qstat","qstat")

        cmd = qstat + " -f"
        self.debug("running "+cmd)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            raise StepError("qstat failed: "+output+"\n")

        jobStrings = []
        curIndex = output.find("Job Id: ")
        if curIndex != -1:
            while True:
                nextIndex = output.find("Job Id: ",curIndex+1)
                if nextIndex == -1:
                    jobStrings.append(output[curIndex:])
                    break
                else:
                    jobStrings.append(output[curIndex:nextIndex])
                    curIndex = nextIndex

        jobs = []
        for jobString in jobStrings:
            job = self._getJob(jobString)
            if self._includeQueue(job.Queue):
                jobs.append(job)

        return jobs

    def _getJob(self, jobString):
        job = ComputingActivity()

        # put multi-lines on one line
        jobString.replace("\n\t","")

        wallTime = None
        usedWallTime = None
	lines = jobString.split("\n")
	for line in lines:
            if line.find("Job Id:") >= 0:
                job.LocalIDFromManager = line[8:]
                # remove the host name
                job.LocalIDFromManager = job.LocalIDFromManager.split(".")[0]
            if line.find("Job_Name =") >= 0:
                job.Name = line.split()[2]
            if line.find("Job_Owner =") >= 0:
                job.LocalOwner = line.split()[2].split("@")[0]
            if line.find("Account_Name =") >= 0:
                job.UserDomain = line.split()[2]
            if line.find("queue =") >= 0:
                job.Queue = line.split()[2]
            if line.find("job_state =") >= 0:
                state = line.split()[2]
                if state == "C":
                    # C is completing after having run
                    job.State = "teragrid:finished"
                elif state == "E":
                    # E is exiting after having run
                    job.State = "teragrid:terminated" #?
                elif state == "Q":
                    job.State = "teragrid:pending"
                elif state == "R":
                    job.State = "teragrid:running"
                elif state == "T":
                    job.State = "teragrid:pending"
                elif state == "Q":
                    job.State = "teragrid:pending"
                elif state == "S":
                    job.State = "teragrid:suspended"
                elif state == "H":
                    job.State = "teragrid:held"
                else:
                    self.warning("found unknown PBS job state '" + state + "'")
                    job.State = "teragrid:unknown"
            if line.find("Resource_List.walltime =") >= 0:
                wallTime = self._getDuration(line.split()[2])
                if job.RequestedSlots != None:
                    job.RequestedTotalWallTime = wallTime * job.RequestedSlots
            # Just ncpus for some PBS installs. Both at other installs, with different values.
            if (line.find("Resource_List.ncpus =") >= 0) or (line.find("Resource_List.nodect =") >= 0):
                requestedSlots = int(line.split()[2])
                if (job.RequestedSlots == None) or (requestedSlots > job.RequestedSlots):
                    job.RequestedSlots = requestedSlots
                    if wallTime != None:
                        job.RequestedTotalWallTime = wallTime * job.RequestedSlots
                    if usedWallTime != None:
                        job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            if line.find("resources_used.walltime =") >= 0:
                usedWallTime = self._getDuration(line.split()[2])
                if job.RequestedSlots != None:
                    job.UsedTotalWallTime = usedWallTime * job.RequestedSlots
            if line.find("resources_used.cput =") >= 0:
                job.UsedTotalCPUTime = self._getDuration(line.split()[2])
            if line.find("qtime =") >= 0:
                job.ComputingManagerSubmissionTime = self._getDateTime(line[line.find("=")+2:])
            if line.find("mtime =") >= 0:
                if job.State == "teragrid:running":
                    job.StartTime = self._getDateTime(line[line.find("=")+2:])
                if (job.State == "teragrid:finished") or (job.State == "teragrid:terminated"):
                    # this is right for terminated since terminated is set on the E state
                    job.ComputingManagerEndTime = self._getDateTime(line[line.find("=")+2:])
            #if line.find("ctime =") >= 0 and \
            #        (job.State == "teragrid:finished" or job.State == "teragrid:terminated"):
            #    job.ComputingManagerEndTime = self._getDateTime(line[line.find("=")+2:])
            #    job.EndTime = job.ComputingManagerEndTime

        return job

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)


    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, aStr):
        # Example: Fri May 30 06:54:25 2008
        # Not quite sure how it handles a different year... guessing
        dayOfWeek = aStr[:3]
        month =     aStr[4:7]
        day =       int(aStr[8:10])
        hour =      int(aStr[11:13])
        minute =    int(aStr[14:16])
        second =    int(aStr[17:19])
        if aStr[19] == ' ':
            year = int(aStr[20:24])
        else:
            year = datetime.datetime.today().year
        
        return datetime.datetime(year=year,
                                 month=self.monthDict[month],
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

#######################################################################################################################

class PbsComputingActivityUpdateStep(ComputingActivityUpdateStep):

    def __init__(self, params):
        ComputingActivityUpdateStep.__init__(self,params)

        self.name = "glue2/pbs/computing_activity_update"
        self.accepts_params["server_logs_dir"] = "the path to the PBS spool/server_logs directory (optional)"

        # caching job information may not be the best idea for systems with very large queues...
        self.activities = {}

    def _run(self):
        try:
            dir_name = self.params["server_logs_dir"]
        except KeyError:
            try:
                dir_name = os.path.join(os.environ["PBS_HOME"],"spool","server_logs")
            except KeyError:
                raise StepError("server_logs_dir not specified and the PBS_HOME environment variable is not set")

        watcher = LogDirectoryWatcher(self._logEntry,dir_name)
        watcher.run()

    def _logEntry(self, log_file_name, entry):
        # log time
        # entry type
        # source (PBS_Server, ...)
        # Svr/Req/Job
        # ? job id (with Job)
        # message
        toks = entry.split(";")
        if len(toks) < 6:
            self.warning("too few tokens in line: %s",entry)
            return
        type = toks[1]
        if type == "0002":
            # batch system/server events
            if toks[5] == "Log closed":
                # move on to the next log
                return False
        elif type == "0008":
            # job events
            self._handleJobEntry(toks)
        elif type == "0010":
            # job resource usage
            pass
        else:
            #self.debug("unknown type %s",type)
            pass
        return True

    def _handleJobEntry(self, toks):
        id = toks[4].split(".")[0]  # just the id part of id.host.name
        try:
            activity = self.activities[id]
        except KeyError:
            activity = ComputingActivity()
            activity.LocalIDFromManager = id
            self.activities[id] = activity
        if "Job Queued" in toks[5]:
            activity.State = "teragrid:pending"
            activity.ComputingManagerSubmissionTime = self._getDateTime(toks[0])
            try:
                m = re.search(" owner = (\w+)@(\S*),",toks[5])  # just the user part of user@host
                activity.LocalOwner = m.group(1)
            except AttributeError:
                self.warning("didn't find owner in log mesage: %s",toks)
                return
            try:
                m = re.search(" job name = (\S+)",toks[5])
                #activity.Name = m.group(1).split(".")[0]  # just the a part of a.b.?
                activity.Name = m.group(1)
            except AttributeError:
                self.warning("didn't find job name in log mesage: %s",toks)
                return
            try:
                m = re.search(" queue = (\S+)",toks[5])
                activity.Queue = m.group(1).split(".")[0]
            except AttributeError:
                self.warning("didn't find queue in log mesage: %s",toks)
                return
        elif "Job Run" in toks[5]:
            activity.State = "teragrid:running"
            activity.StartTime = self._getDateTime(toks[0])
        elif "Job deleted" in toks[5]:
            activity.State = "teragrid:terminated"
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "JOB_SUBSTATE_EXITING" in toks[5]:
            activity.State = "teragrid:finished"
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "Job sent signal SIGKILL on delete" in toks[5]:
            # job ran too long and was killed
            activity.State = "teragrid:terminated"
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "Job Modified" in toks[5]:
            # when nodes aren't available, log has jobs that quickly go from Job Queued to Job Run to Job Modified
            # and the jobs are pending after this
            if activity.State == "teragrid:running":
                activity.State = "teragrid:pending"
                activity.StartTime = None
            else:
                self.warning("not sure how to handle log event: %s",toks)
        else:
            self.warning("unhandled log event: %s",toks)
            return

        if activity.Queue is None or self._includeQueue(activity.Queue):
            self.output(activity)
            

    def _getDateTime(self, dt_str):
        # Example: 06/10/2012 16:17:41
        month = int(dt_str[:2])
        day = int(dt_str[3:5])
        year = int(dt_str[6:10])
        hour = int(dt_str[11:13])
        minute = int(dt_str[14:16])
        second = int(dt_str[17:19])
        return datetime.datetime(year=year,
                                 month=month,
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

#######################################################################################################################
