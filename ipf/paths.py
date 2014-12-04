
###############################################################################
#   Copyright 2014 The University of Texas at Austin                          #
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
import sys

#######################################################################################################################

path = os.path.abspath(__file__)
path = os.path.split(path)[0]    # drop file name
IPF_PARENT_PATH = path

if "IPF_ETC_PATH" in os.environ:
    IPF_ETC_PATH = os.environ["IPF_ETC_PATH"]
else:
    IPF_ETC_PATH = os.path.join(IPF_PARENT_PATH,"etc","ipf")

if "IPF_VAR_PATH" in os.environ:
    IPF_VAR_PATH = os.environ["IPF_VAR_PATH"]
else:
    IPF_VAR_PATH = os.path.join(IPF_PARENT_PATH,"var","ipf")
# just use the ipf var directory
IPF_LOG_PATH = IPF_VAR_PATH

if "IPF_WORKFLOW_PATHS" in os.environ:
    IPF_WORKFLOW_PATHS = os.environ["IPF_WORKFLOW_PATHS"].split(":")
else:
    IPF_WORKFLOW_PATHS = []
if "/etc/ipf/workflow" not in IPF_WORKFLOW_PATHS:
    IPF_WORKFLOW_PATHS.append("/etc/ipf/workflow")
if os.path.join(IPF_ETC_PATH,"workflow") not in IPF_WORKFLOW_PATHS:
    IPF_WORKFLOW_PATHS.append(os.path.join(IPF_ETC_PATH,"workflow"))
