
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

import os
import sqlite3
import re

from .. import nimbus

#######################################################################################################################

class ComputingActivitiesStep(nimbus.ComputingActivitiesStep):
    def __init__(self):
        nimbus.ComputingActivitiesStep.__init__(self)

    def _run(self):
        activities = nimbus.ComputingActivitiesStep._run(self)
        for activity in activities:
            try:
                m = re.search("/O=Auto/OU=FutureGridNimbus/CN=(\S+)",activity.LocalOwner)
                activity.Owner = m.group(1)
            except AttributeError:
                # only query the Nimbus sqlite database when necessary
                try:
                    activity.Owner = _lookupOwner(self.nimbus_dir,activity.LocalOwner)
                except:
                    self.warning("couldn't derive Owner from LocalOwner %s",activity.LocalOwner)
        return activities

#######################################################################################################################

class ComputingActivityUpdateStep(nimbus.ComputingActivityUpdateStep):
    def __init__(self):
        nimbus.ComputingActivityUpdateStep.__init__(self)

    def output(self, activity):
        try:
            m = re.search("/O=Auto/OU=FutureGridNimbus/CN=(\S+)",activity.LocalOwner)
            activity.Owner = m.group(1)
        except AttributeError:
            # only query the Nimbus sqlite database when necessary
            try:
                activity.Owner = _lookupOwner(self.nimbus_dir,activity.LocalOwner)
            except:
                self.warning("couldn't derive Owner from LocalOwner %s",activity.LocalOwner)
        computing_activity.ComputingActivityUpdateStep.output(self,activity)

#######################################################################################################################

def _lookupOwner(nimbus_dir,dn):
    conn = sqlite3.connect(os.path.join(nimbus_dir,"cumulus","etc","authz.db"))
    c = conn.cursor()
    c.execute("select friendly_name from user_alias where alias_type = 2 and alias_name = '%s'" % dn)
    name = c.fetchone()[0]
    c.close()
    conn.close()
    return name.encode("utf-8")
                            
#######################################################################################################################
