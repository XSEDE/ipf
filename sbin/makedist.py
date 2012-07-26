#!/bin/env python

import os
import shutil
import tempfile

version = "0.5"

os.umask(0)

temp_path = tempfile.mkdtemp()

path = os.path.join(temp_path,"ipf-"+version)
os.mkdir(path,0755)

shutil.copy("LICENSE-2.0.txt",path)
shutil.copy("INSTALL.txt",path)
shutil.copy("install.py",path)

ig=shutil.ignore_patterns("*~","*.pyc","*.pem")

shutil.copytree("bin",os.path.join(path,"bin"),ignore=ig)
shutil.copytree("lib",os.path.join(path,"lib"),ignore=ig)
shutil.copytree("libexec",os.path.join(path,"libexec"),ignore=ig)
shutil.copytree("etc",os.path.join(path,"etc"),ignore=ig)

shutil.copytree(os.path.join("..","mtk","lib","mtk","amqp_0_9_1"),
                os.path.join(path,"lib","mtk","amqp_0_9_1"),
                ignore=ig)
shutil.copy(os.path.join("..","mtk","lib","mtk","__init__.py"),
            os.path.join(path,"lib","mtk","__init__.py"))

dir = os.getcwd()
os.chdir(temp_path)
os.system("tar czf "+os.path.join(dir,"ipf-"+version+".tar.gz")+" ipf-"+version)
os.chdir(dir)

shutil.rmtree(temp_path)
