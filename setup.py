#!/usr/bin/env python

# $ cd $IPF_HOME/lib
# $ ln -s $MTK_HOME/lib/mtk .
#
# To create the package:
# 
# $ ./setup.py sdist
#
# To install the package:
#
# $ python virtualenv.py $HOME/tmp/ipf-0.5-install
# $ cd $HOME/tmp
# $ tar xzf ~/ipf/dist/ipf-0.5.tar.gz 
# $ cd ipf-0.5
# $ $HOME/tmp/ipf-0.5-install/bin/python setup.py install


from distutils.core import setup
import distutils.dir_util
import distutils.sysconfig
import os
import sys

def isPackage(path):
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, '__init__.py'))

def findPackages(path, base="", exclude=[]):
    packages = []
    for name in os.listdir(path):
        dir = os.path.join(path,name)
        if not isPackage(dir):
            continue
        if base is "":
            module_name = name
        else:
            module_name = "%s.%s" % (base,name)
        if module_name in exclude:
            continue
        packages.append(module_name)
        packages.extend(findPackages(os.path.join(path,name),module_name,exclude))
    return packages

def findFiles(path, exclude=[]):
    data_files = []
    files = []
    for name in os.listdir(path):
        if name.endswith("~"):  # bit of a hack
            continue
        child_path = os.path.join(path,name)
        if os.path.isfile(child_path):
            files.append(child_path)
    data_files.append((path,files))
    for name in os.listdir(path):
        child_path = os.path.join(path,name)
        if os.path.isdir(child_path):
            data_files.extend(findFiles(child_path,exclude))
    return data_files

packages=[]
if sys.argv[1] != "install":
    packages.append("ipf")
    packages.extend(findPackages("lib/steps","steps"))
    packages.extend(findPackages("lib/glue2","glue2"))
    packages.extend(findPackages("lib/mtk/amqp_0_9_1","mtk.amqp_0_9_1"))

data_files = []
if sys.argv[1] != "install":
    data_files.append("",["LICENSE-2.0.txt"])
    data_files.append(("etc",["etc/logging.conf","etc/teragrid_glue_2.0_r02.xsd","etc/ctss_glue2_envelope.xsd"]))
    data_files.extend(findFiles("etc/workflow"))

setup(name="ipf",
      version="0.5",
      description="Information Publishing Framework",
      author="Warren Smith",
      author_email="wsmith@tacc.utexas.edu",
      package_dir={"": "lib"},
      data_files=data_files,
      packages=packages,
      scripts=["bin/run_workflow.py","bin/step_info.py"],
      )

if sys.argv[1] == "install":
    created = distutils.dir_util.mkpath(os.path.join(sys.prefix,"var"))
    print("created directories: %s" % created)
