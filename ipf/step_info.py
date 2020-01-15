
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
from functools import reduce

min_version = (3,6)
max_version = (3,9)

if sys.version_info < min_version or sys.version_info > max_version:
    print(stderr,"Python version 3.6 or newer is required")
    sys.exit(1)

from ipf.catalog import catalog

#######################################################################################################################

if __name__ == "__main__":
    opt = optparse.OptionParser(usage="usage: %prog [options]")
    opt.add_option("-n","--name_pattern",action="store",type="string",dest="name_pattern",default=".*",
                   help="a Python regular expression to use to select steps by name (default .*)")
    opt.add_option("-i","--input_pattern",action="store",type="string",dest="input_pattern",default=".*",
                   help="a Python regular expression to use to select steps by type of input document (default .*)")
    opt.add_option("-o","--output_pattern",action="store",type="string",dest="output_pattern",default=".*",
                   help="a Python regular expression to use to select steps by type of output document (default .*)")
    (options,args) = opt.parse_args()

    for step_name in sorted(catalog.steps):
        step = catalog.steps[step_name]()
        if re.search(options.name_pattern,step.name) == None:
            continue
        if not reduce(lambda b1,b2: b1 or b2,
                      [re.search(options.input_pattern,cls.__module__+"."+cls.__name__) is not None for cls in step.requires],
                      False):
            continue
        if not reduce(lambda b1,b2: b1 or b2,
                      [re.search(options.output_pattern,cls.__module__+"."+cls.__name__) is not None for cls in step.produces],
                      False):
            continue
        print(step)
