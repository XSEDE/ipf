
import os
from setuptools import setup
from setuptools import find_packages

def readme():
    with open("README.rst") as f:
        return f.read()

def _getManifestFileName():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    return os.path.join(path,"MANIFEST.in")

def _createManifest():
    f = open(_getManifestFileName(),"w")
    f.write("""
include ipf/etc/ipf/workflow/xsede/teragrid_software.json
include ipf/etc/ipf/workflow/xsede/teragrid_software_periodic.json
    """)
    f.close()

def _deleteManifest():
    os.remove(_getManifestFileName())

def _getSetupCfgFileName():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    return os.path.join(path,"setup.cfg")

def _createSetupCfg():
    f = open(_getSetupCfgFileName(),"w")
    f.write("""
[bdist_rpm]
requires =
    ipf-xsede-glue2 >= 1.0b1
    ipf-xsede-glue2 < 2.0
    """)
    f.close()

def _deleteSetupCfg():
    os.remove(_getSetupCfgFileName())

if __name__ == "__main__":
    _createManifest()
    _createSetupCfg()
    description="XSEDE workflows to publish TeraGrid kits and local software using the Information Publishing Framework"
    setup(name="ipf-xsede-teragrid-kitssoftware",
          version="1.0b1",
          description=description,
          long_description=description,
          classifiers=[
              #"Development Status :: 5 - Production/Stable",
              "Development Status :: 4 - Beta",
              #"Development Status :: 3 - Alpha",
              "License :: OSI Approved :: Apache Software License",
              "Programming Language :: Python :: 2",
              "Topic :: System :: Monitoring",
          ],
          keywords="monitoring information gathering publishing glue2 xsede",
          url="https://bitbucket.org/wwsmith/ipf",
          author="Warren Smith",
          author_email="wsmith@tacc.utexas.edu",
          license="Apache",
          packages=[],
          install_requires=["ipf-xsede-glue2"],
          include_package_data=True,
          zip_safe=False)
    _deleteManifest()
    _deleteSetupCfg()




