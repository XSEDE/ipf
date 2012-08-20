#!/bin/env python

import glob
import os
import shutil
import tempfile

version = "1.0b3"

os.umask(0)

temp_path = tempfile.mkdtemp()

path = os.path.join(temp_path,"futuregrid_glue2-"+version)
os.mkdir(path,0755)

shutil.copy("LICENSE-2.0.txt",path)
shutil.copy("INSTALL_futuregrid.txt",os.path.join(path,"INSTALL.txt"))
shutil.copy("install.py",path)

ig=shutil.ignore_patterns("*~","*.pyc","*.pem")

shutil.copytree("bin",os.path.join(path,"bin"),ignore=ig)
shutil.copytree("lib",os.path.join(path,"lib"),ignore=ig)
shutil.copytree("libexec",os.path.join(path,"libexec"),ignore=ig)
shutil.copytree(os.path.join("etc","workflow","futuregrid"),
                os.path.join(path,"etc","workflow","futuregrid"),ignore=ig)
shutil.copy(os.path.join("etc","logging.conf"),os.path.join(path,"etc"))
shutil.copy(os.path.join("etc","ca_certs.pem"),os.path.join(path,"etc"))

shutil.copytree(os.path.join("..","mtk","lib","mtk","amqp_0_9_1"),
                os.path.join(path,"lib","mtk","amqp_0_9_1"),
                ignore=ig)
shutil.copy(os.path.join("..","mtk","lib","mtk","__init__.py"),
            os.path.join(path,"lib","mtk","__init__.py"))

dir = os.getcwd()
os.chdir(temp_path)
os.system("tar czf "+os.path.join(dir,"futuregrid_glue2-"+version+".tar.gz")+" futuregrid_glue2-"+version)
os.chdir(dir)

shutil.rmtree(temp_path)
