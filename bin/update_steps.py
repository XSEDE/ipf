#!/usr/bin/env python

import json
import os
import sys
import ConfigParser

from ipf.engine import readConfig
from ipf.workflow import ProgramStep

#######################################################################################################################

ipfHome = os.environ.get("IPF_HOME")
if ipfHome == None:
    sys.stderr.write("IPF_HOME environment variable not set\n")
    sys.exit(1)

#######################################################################################################################

def updateKnownSteps():
    known_steps = readKnownSteps()
    dirs = getStepDirectories()

    steps = set()
    updated = False
    for dir in dirs:
        #print("under directory "+dir)
        for dirname, dirnames, filenames in os.walk(dir,followlinks=True):
            for filename in filenames:
                if filename.endswith("~"):
                    # bit of a hack for now
                    continue
                executable = os.path.join(dirname,filename)
                if not os.access(executable,os.X_OK):
                    continue
                mtime = os.path.getmtime(executable)
                #print("  "+executable)
                if executable in known_steps:
                    #print("    known")
                    if mtime == known_steps[executable].modification_time:
                        steps.add(known_steps[executable])
                        continue
                step = ProgramStep()
                step.modification_time = mtime
                try:
                    print("    discovering %s" % executable)
                    step.discover(executable)
                except:
                    pass
                steps.add(step)
                updated = True
    if len(steps) != len(known_steps):
        updated = True
    if updated:
        print("updating known steps file")
        writeKnownSteps(steps)
    else:
        print("no updated needed to known steps file")

def getStepDirectories():
    config = readConfig()
    try:
        dirs = []
        for dir in config.get("ipf","step_dirs").split(","):
            if os.path.isabs(dir):
                dirs.append(dir)
            else:
                dirs.append(os.path.join(ipfHome,dir))
    except ConfigParser.Error:
        dirs = [os.path.join(ipfHome,"libexec")]

    return dirs

def readKnownSteps():
    steps = {}
    try:
        file = open(os.path.join(ipfHome,"var","known_steps.json"))
        doc = json.load(file)
        file.close()
    except IOError:
        # file not found
        return known_steps
    except ValueError:
        # bad json in file
        return known_steps

    for step_doc in doc:
        step = ProgramStep()
        step.fromJson(step_doc)
        steps[step.executable] = step

    return steps

def writeKnownSteps(steps):
    file = open(os.path.join(ipfHome,"var","known_steps.json"),"w")
    doc = []
    for step in steps:
        doc.append(step.toJson())
    json.dump(doc,file,sort_keys=True,indent=4)
    file.close()

#######################################################################################################################

if __name__ == "__main__":
    updateKnownSteps()
    
