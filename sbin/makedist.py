#!/bin/env python

import os
import shutil
import tempfile

version = "2.0.0"

os.umask(0)

path = tempfile.mkdtemp()
print(path)

gpath = os.path.join(path,"glue2-"+version)
os.mkdir(gpath,0755)

shutil.copyfile("LICENSE-2.0.txt",os.path.join(gpath,"LICENSE-2.0.txt"))

ig=shutil.ignore_patterns("*~","*.pyc","*.pem")

shutil.copytree("bin",os.path.join(gpath,"bin"),ignore=ig)
shutil.copytree("libexec",os.path.join(gpath,"libexec"),ignore=ig)
shutil.copytree("lib",os.path.join(gpath,"lib"),ignore=ig)
shutil.copytree("etc",os.path.join(gpath,"etc"),ignore=ig)

os.mkdir(os.path.join(gpath,"var"))

dir = os.getcwd()
os.chdir(path)
os.system("tar czf "+os.path.join(dir,"glue2-"+version+".tar.gz")+" glue2-"+version)
os.chdir(dir)

shutil.rmtree(path)
