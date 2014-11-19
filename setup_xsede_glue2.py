
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

if __name__ == "__main__":
    _createManifest()
    description="XSEDE GLUE v2.0 workflows for the Information Publishing Framework"
    setup(name="ipf-xsede-glue2",
          #version="1.0"
          version="1.0a10",
          description=description,
          long_description=description,
          classifiers=[
              #"Development Status :: 5 - Production/Stable",
              #"Development Status :: 4 - Beta",
              "Development Status :: 3 - Alpha",
              "License :: OSI Approved :: Apache Software License",
              "Programming Language :: Python :: 2",
              "Topic :: System :: Monitoring",
          ],
          keywords="monitoring information gathering publishing glue2 xsede",
          url="https://bitbucket.org/wwsmith/ipf",
          author="Warren Smith",
          author_email="wsmith@tacc.utexas.edu",
          license="Apache",
          packages=["ipf.teragrid"],
          install_requires=["ipf"],
          include_package_data=True,
          zip_safe=False)
    _deleteManifest()


