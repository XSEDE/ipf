
import os
from setuptools import setup
from setuptools import find_packages

def _getManifestFileName():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    return os.path.join(path,"MANIFEST.in")

def _createManifest():
    f = open(_getManifestFileName(),"w")
    f.write("""
include ipf/etc/ipf/xsede/ca_certs.pem
include ipf/etc/ipf/workflow/xsede/glue2/*.json
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
    ipf >= 1.0b2
    ipf < 2.0
    """)
    f.close()

def _deleteSetupCfg():
    os.remove(_getSetupCfgFileName())

def workflow_paths(directory):
    return filter(lambda path: os.path.isfile(path) and path.endswith(".json"),
                  map(lambda file: os.path.join(directory,file),os.listdir(directory)))

if __name__ == "__main__":
    _createManifest()
    _createSetupCfg()
    description="XSEDE GLUE v2.0 workflows for the Information Publishing Framework"
    setup(name="ipf-xsede-glue2",
          version="1.0b2",
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
          # this is dumb, but it gets the right files from etc into the rpm:
          #   ipf.etc results in the files under ipf/etc/in the MANIFEST.in being included in the rpm
          packages=["ipf.teragrid","ipf.etc"],
          install_requires=["ipf"],
          include_package_data=False,
          data_files = [
              ("/etc/ipf/xsede",["ipf/etc/ipf/xsede/ca_certs.pem"]),
              ("/etc/ipf/workflow/xsede/glue2",workflow_paths("ipf/etc/ipf/workflow/xsede/glue2"))
          ],
          zip_safe=False)
    _deleteManifest()
    _deleteSetupCfg()
