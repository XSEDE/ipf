
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

import optparse
import re
import sys

min_version = (2,6)
max_version = (2,9)

if sys.version_info < min_version or sys.version_info > max_version:
    print(stderr,"Python version 2.6 or 2.7 is required")
    sys.exit(1)

from ipf.engine import WorkflowEngine

#######################################################################################################################

def usage():
    print("usage: step_info.py [step type]*")

if __name__ == "__main__":
    opt = optparse.OptionParser(usage="usage: %prog [options]")
    opt.add_option("-n","--name_pattern",action="store",type="string",dest="name_pattern",default=".*",
                   help="a Python regular expression to use to select steps by name (default .*)")
    opt.add_option("-c","--class_pattern",action="store",type="string",dest="class_pattern",default=".*",
                   help="a Python regular expression to use to select steps by module.class (default .*)")
    opt.add_option("-i","--input_type_pattern",action="store",type="string",dest="input_type_pattern",default=".*",
                   help="a Python regular expression to use to select steps by type of input document (default .*)")
    opt.add_option("-o","--output_type_pattern",action="store",type="string",dest="output_type_pattern",default=".*",
                   help="a Python regular expression to use to select steps by type of output document (default .*)")
    (options,args) = opt.parse_args()

    engine = WorkflowEngine()
    steps = engine.readKnownSteps()
    for step_name in steps:
        step = steps[step_name]({})
        if re.search(options.name_pattern,step.name) == None:
            continue
        if re.search(options.class_pattern,step.__module__+"."+step.__class__.__name__) == None:
            continue
        if not reduce(lambda b1,b2: b1 or b2,
                      map(lambda type: re.search(options.input_type_pattern,type) is not None,
                          step.requires_types),
                      False):
            continue
        if not reduce(lambda b1,b2: b1 or b2,
                      map(lambda type: re.search(options.output_type_pattern,type) is not None,
                          step.produces_types),
                      False):
            continue
        print(step)
