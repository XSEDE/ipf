
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

    def __init__(self):
        ComputingActivitiesStep.__init__(self)

        self._acceptParameter("qstat","the path to the PBS qstat program (default 'qstat')",False)

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

        m = re.search("Job Id: (\S+)",jobString)
        if m is not None:
            # remove the host name
            job.LocalIDFromManager = m.group(1).split(".")[0]
        m = re.search("Job_Name = (\S+)",jobString)
        if m is not None:
            job.Name = m.group(1)
        m = re.search("Job_Owner = (\S+)",jobString)
        if m is not None:
            # remove the host name
            job.LocalOwner = m.group(1).split("@")[0]
        m = re.search("Account_Name = (\S+)",jobString)
        if m is not None:
            job.UserDomain = m.group(1)
        m = re.search("queue = (\S+)",jobString)
        if m is not None:
            job.Queue = m.group(1)
        m = re.search("job_state = (\S+)",jobString)
        if m is not None:
            state = m.group(1)
            if state == "C":
                # C is completing after having run
                job.State = ComputingActivity.STATE_FINISHED
            elif state == "E":
                # E is exiting after having run
                job.State = ComputingActivity.STATE_TERMINATED #?
            elif state == "Q":
                job.State = ComputingActivity.STATE_PENDING
            elif state == "R":
                job.State = ComputingActivity.STATE_RUNNING
            elif state == "T":
                job.State = ComputingActivity.STATE_PENDING
            elif state == "Q":
                job.State = ComputingActivity.STATE_PENDING
            elif state == "S":
                job.State = ComputingActivity.STATE_SUSPENDED
            elif state == "H":
                job.State = ComputingActivity.STATE_HELD
            else:
                self.warning("found unknown PBS job state '%s'",state)
                job.State = ComputingActivity.STATE_UNKNOWN
        # Just ncpus for some PBS installs. Both at other installs, with different values.
        m = re.search("Resource_List.ncpus = (\d+)",jobString)
        if m is not None:
            cpus = int(m.group(1))
        else:
            cpus = None
        m = re.search("Resource_List.nodect = (\d+)",jobString)
        if m is not None:
            job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.nodes = (\d+)",jobString)
        if m is not None:
            requested_slots = int(m.group(1))
            if job.RequestedSlots is None or requested_slots > job.RequestedSlots:
                job.RequestedSlots = int(m.group(1))
        m = re.search("Resource_List.nodes = (\d+):ppn=(\d+)",jobString)
        if m is not None:
            job.RequestedSlots = int(m.group(1)) * int(m.group(2))
        m = re.search("Resource_List.walltime = (\S+)",jobString)
        if m is not None:
            wall_time = self._getDuration(m.group(1))
            if job.RequestedSlots is not None:
                job.RequestedTotalWallTime = wall_time * job.RequestedSlots
        m = re.search("resource_used.walltime = (\S+)",jobString)
        if m is not None:
            used_wall_time = self._getDuration(m.group(1))
            if job.RequestedSlots is not None:
                job.UsedTotalWallTime = used_wall_time * job.RequestedSlots
        m = re.search("resource_used.cput = (\S+)",jobString)
        if m is not None:
            job.UsedTotalCPUTime = self._getDuration(m.group(1))
        m = re.search("qtime.cput = (\S+)",jobString)
        if m is not None:
            job.ComputingManagerSubmissionTime = self._getDateTime(m.group(1))
        m = re.search("mtime = (\w+ \w+ \d+ \d+:\d+:\d+ \d+)",jobString)
        if m is not None:
            if job.State == ComputingActivity.STATE_RUNNING:
                job.StartTime = self._getDateTime(m.group(1))
            if (job.State == ComputingActivity.STATE_FINISHED) or (job.State == ComputingActivity.STATE_TERMINATED):
                # this is right for terminated since terminated is set on the E state
                job.ComputingManagerEndTime = self._getDateTime(m.group(1))
        #m = re.search("ctime = (\S+)",jobString)
        #if m is not None:
        #    if line.find("ctime =") >= 0 and \
        #           (job.State == ComputingActivity.STATE_FINISHED or job.State == ComputingActivity.STATE_TERMINATED):
        #        job.ComputingManagerEndTime = self._getDateTime(m.group(1))
        #        job.EndTime = job.ComputingManagerEndTime

        return job

    def _getDuration(self, dStr):
        (hour,minute,second)=dStr.split(":")
        return int(hour)*60*60 + int(minute)*60 + int(second)


    monthDict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

    def _getDateTime(self, dt_str):
        # Example: Fri May 30 06:54:25 2008
        # Not quite sure how it handles a different year... guessing

        m = re.search("(\w+) (\w+) (\d+) (\d+):(\d+):(\d+) (\d+)",dt_str)
        if m is None:
            raise StepError("can't parse '%s' as a date/time" % dt_str)
        dayOfWeek = m.group(1)
        month =     self.monthDict[m.group(2)]
        day =       int(m.group(3))
        hour =      int(m.group(4))
        minute =    int(m.group(5))
        second =    int(m.group(6))
        year =      int(m.group(7))
        
        return datetime.datetime(year=year,
                                 month=month,
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

#######################################################################################################################

class PbsComputingActivityUpdateStep(ComputingActivityUpdateStep):

    def __init__(self):
        ComputingActivityUpdateStep.__init__(self)

        self._acceptParameter("server_logs_dir","the path to the PBS spool/server_logs directory (optional)",False)

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
            activity.State = ComputingActivity.STATE_PENDING
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
            activity.State = ComputingActivity.STATE_RUNNING
            activity.StartTime = self._getDateTime(toks[0])
        elif "Job deleted" in toks[5]:
            activity.State = ComputingActivity.STATE_TERMINATED
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "JOB_SUBSTATE_EXITING" in toks[5]:
            activity.State = ComputingActivity.STATE_FINISHED
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "Job sent signal SIGKILL on delete" in toks[5]:
            # job ran too long and was killed
            activity.State = ComputingActivity.STATE_TERMINATED
            activity.ComputingManagerEndTime = self._getDateTime(toks[0])
            del self.activities[id]
        elif "Job Modified" in toks[5]:
            # when nodes aren't available, log has jobs that quickly go from Job Queued to Job Run to Job Modified
            # and the jobs are pending after this
            if activity.State == ComputingActivity.STATE_RUNNING:
                activity.State = ComputingActivity.STATE_PENDING
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
        m = re.search("(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)",dt_str)
        if m is None:
            raise StepError("can't parse '%s' as a date/time" % dt_str)
        month = int(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        second = int(m.group(6))
        return datetime.datetime(year=year,
                                 month=month,
                                 day=day,
                                 hour=hour,
                                 minute=minute,
                                 second=second,
                                 tzinfo=localtzoffset())

#######################################################################################################################
