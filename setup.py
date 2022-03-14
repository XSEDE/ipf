import os
from setuptools import setup
from setuptools import find_packages

# install locally as links back to this directory
# python setup.py develop
# python setup.py develop --uninstall

# install in editable mode for development/testing pip install -e .

# Create a pypi account and have a $HOME/.pypirc with that info

# To register the project in pypi (just once):
# $ python setup.py register

# To create a source distribution and upload to pypi:
# $ python setup.py sdist upload

def readme():
    with open("README.md") as f:
        return f.read()

def _getManifestFileName():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    return os.path.join(path,"MANIFEST.in")

# manifest specifies files to include in the source distribution
def _createManifest():
    f = open(_getManifestFileName(),"w")
    f.write("""
include README.md
include LICENSE-2.0.txt
include ipf/bin/ipf_workflow
include ipf/bin/ipf_configure_xsede
include ipf/etc/ipf/logging.conf
include ipf/etc/ipf/workflow/*.json
include ipf/etc/ipf/workflow/templates/glue2/*.json
include ipf/etc/ipf/init.d/ipf-WORKFLOW
include ipf/etc/ipf/xsede/ca_certs.pem
include ipf/var/ipf/README.txt
    """)
    f.close()

def _deleteManifest():
    os.remove(_getManifestFileName())

def _getSetupCfgFileName():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    return os.path.join(path,"setup.cfg")

# A setup.cfg file seems to be the best way to define RPM Requires
def _createSetupCfg():
    f = open(_getSetupCfgFileName(),"w")
    f.write("""
[bdist_rpm]
requires = python-amqp >= 1.4
    python-dateutil
    """)
    f.close()

def _deleteSetupCfg():
    os.remove(_getSetupCfgFileName())

def workflow_paths(directory):
    return [path for path in [os.path.join(directory,file) for file in os.listdir(directory)] if os.path.isfile(path) and path.endswith(".json")]

if __name__ == "__main__":
    _createManifest()
    _createSetupCfg()
    setup(name="ipf",
          version="1.7a1",
          description="The Information Publishing Framework",
          long_description=readme(),
          classifiers=[
              "Development Status :: 5 - Production/Stable",
              "License :: OSI Approved :: Apache Software License",
              "Programming Language :: Python :: 2",
              "Topic :: System :: Monitoring",
          ],
          keywords="monitoring information gathering publishing glue2",
          url="https://bitbucket.org/wwsmith/ipf",
          author="Eric Blau, Warren Smith",
          author_email="blau@anl.gov",
          license="Apache",
          packages=["ipf","ipf.glue2","ipf.xsede","ipf.xsede.test"],
          install_requires=["amqp >=1.4,<2","python-dateutil"],
          entry_points={
              "console_scripts": ["ipf_workflow=ipf.run_workflow:main",
                                  "ipf_configure_xsede=ipf.xsede.configure_workflows:configure"],
          },
          #include_package_data=True,
          include_package_data=False,
          # data files only applies to the rpm
          data_files = [
              ("/etc/ipf",["ipf/etc/ipf/logging.conf"]),
              ("/etc/ipf/xsede",["ipf/etc/ipf/xsede/ca_certs.pem"]),
              ("/etc/ipf/workflow",workflow_paths("ipf/etc/ipf/workflow")),
              ("/etc/ipf/workflow/glue2",[]),
              ("/etc/ipf/workflow/templates/glue2",workflow_paths("ipf/etc/ipf/workflow/templates/glue2")),
              ("/etc/ipf/init.d",["ipf/etc/ipf/init.d/ipf-WORKFLOW"]),
              ("/var/ipf",[])
          ],
          zip_safe=False)
    _deleteManifest()
    _deleteSetupCfg()






