
import os
import shutil
import stat
import sys

def checkVersion():
    min_version = (2,6)
    max_version = (2,9)
    if sys.version_info < min_version or sys.version_info > max_version:
        raise Exception("Python version between %d.%d and %d.%d is required\n" %
                         (min_version[0],min_version[1],max_version[0],max_version[1]))

substitutions = {}

def substitute(text):
    for key in substitutions:
        text = text.replace("@%s@" % key,substitutions[key])
    return text

def copyReplace(in_name, out_name):
    in_file = open(in_name,"r")
    out_file = open(out_name,"w")

    out_file.write(substitute(in_file.read()))

    in_file.close()
    out_file.close()

    shutil.copystat(in_name,out_name)

def ignoreNone(dir_name, file_names):
    return []

def copyReplaceTree(in_dir, out_dir, ignore=ignoreNone):
    file_names = os.listdir(in_dir)
    exclude_names = ignore(in_dir,file_names)
    file_names = filter(lambda x:x not in exclude_names,file_names)

    os.mkdir(out_dir)
    for name in file_names:
        in_path = os.path.join(in_dir,name)
        out_path = os.path.join(out_dir,name)
        if os.path.isfile(in_path):
            copyReplace(in_path,out_path)
        elif os.path.isdir(in_path):
            copyReplaceTree(in_path,out_path)
        else:
            raise Exception("copyReplaceTree can't handle file %s",in_path)

generic_workflow = """#!/bin/sh -l

export PYTHONPATH=@install_dir@/lib

@python@ @install_dir@/libexec/run_workflow.py @install_dir@/@workflow_dir@/@workflow@.json >> @install_dir@/var/@workflow@.log 2>&1
"""

generic_daemon = """#!/bin/sh -l

export PYTHONPATH=@install_dir@/lib

@python@ @install_dir@/libexec/run_workflow_daemon.py @install_dir@/@workflow_dir@/@workflow@.json >> @install_dir@/var/@workflow@.log 2>&1
"""

pbs_workflow = """#!/bin/sh -l

module load torque

export PYTHONPATH=@install_dir@/lib

@python@ @install_dir@/libexec/run_workflow.py @install_dir@/@workflow_dir@/@workflow@.json >> @install_dir@/var/@workflow@.log 2>&1
"""

pbs_daemon = """#!/bin/sh -l

module load torque

export PYTHONPATH=@install_dir@/lib

@python@ @install_dir@/libexec/run_workflow_daemon.py @install_dir@/@workflow_dir@/@workflow@.json >> @install_dir@/var/@workflow@.log 2>&1
"""

def generateScript(workflow_dir, file_name, install_dir):
    if "pbs" in file_name:
        if "updates" in file_name:
            text = pbs_daemon
        else:
            text = pbs_workflow
    elif "nimbus" in file_name:
        if "updates" in file_name:
            text = generic_daemon
        else:
            text = generic_workflow
    else:
        raise Exception("can't generate script for workflow file %s in %s" % (file_name,workflow_dir))

    substitutions["workflow_dir"] = workflow_dir
    workflow = os.path.splitext(file_name)[0]
    substitutions["workflow"] = workflow
    script = os.path.join(install_dir,"bin",workflow+".sh")

    if os.path.exists(script):
        raise Exception("already generated the script %s, won't overwrite with another workflow" % script)

    file = open(script,"w")
    file.write(substitute(text))
    file.close()
    os.chmod(script,os.stat(script).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def generateScripts(workflow_dir, install_dir):
    for name in os.listdir(workflow_dir):
        path = os.path.join(workflow_dir,name)
        if os.path.isfile(path):
            generateScript(workflow_dir,name,install_dir)
        elif os.path.isdir(path):
            generateScripts(path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("usage: python install.py <install directory>\n")
        sys.exit(1)

    checkVersion()

    install_dir = sys.argv[1]
    print("installing to %s" % install_dir)

    substitutions["python"] = sys.executable
    substitutions["install_dir"] = install_dir

    ig=shutil.ignore_patterns("*~","*.pyc") # for testing - shouldn't need in final version
    shutil.copytree("libexec",os.path.join(install_dir,"libexec"),ignore=ig)
    shutil.copytree("lib",os.path.join(install_dir,"lib"),ignore=ig)
    shutil.copytree("etc",os.path.join(install_dir,"etc"),ignore=ig)
    copyReplaceTree("bin",os.path.join(install_dir,"bin"),ignore=ig)

    generateScripts(os.path.join("etc","workflow","futuregrid"),install_dir)

    shutil.copy("LICENSE-2.0.txt",install_dir)
    shutil.copy("INSTALL.txt",install_dir)

    os.mkdir(os.path.join(install_dir,"var"))

