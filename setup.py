
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
    with open("README.rst") as f:
        return f.read()

def _getManifestFileName():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    return os.path.join(path,"MANIFEST.in")

def _createManifest():
    f = open(_getManifestFileName(),"w")
    f.write("""
include README.rst
include LICENSE-2.0.txt
include ipf/etc/ipf/logging.conf
include ipf/etc/ipf/workflow/*.json
include ipf/etc/ipf/workflow/glue2/*.json
include ipf/etc/init.d/ipf-WORKFLOW
include ipf/var/ipf/README.txt
include ipf/var/log/ipf/README.txt
    """)
    f.close()

def _deleteManifest():
    os.remove(_getManifestFileName())


if __name__ == "__main__":
    _createManifest()
    setup(name="ipf",
          #version="1.0"
          version="1.0a10",
          description="The Information Publishing Framework",
          long_description=readme(),
          classifiers=[
              #"Development Status :: 5 - Production/Stable",
              #"Development Status :: 4 - Beta",
              "Development Status :: 3 - Alpha",
              "License :: OSI Approved :: Apache Software License",
              "Programming Language :: Python :: 2",
              "Topic :: System :: Monitoring",
          ],
          keywords="monitoring information gathering publishing glue2",
          url="https://bitbucket.org/wwsmith/ipf",
          author="Warren Smith",
          author_email="wsmith@tacc.utexas.edu",
          license="Apache",
          packages=["ipf","ipf.glue2"],
          install_requires=["mtk"],
          entry_points={
              "console_scripts": ["ipf_workflow=ipf.run_workflow:main"],
          },
          include_package_data=True,
          zip_safe=False)
    _deleteManifest()






