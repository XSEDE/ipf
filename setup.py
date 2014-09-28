from setuptools import setup
from setuptools import find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='ipf',
      #version='1.0',
      version='1.0b',
      description='The Information Publishing Framework',
      long_description=readme(),
      classifiers=[
        #'Development Status :: 5 - Production/Stable',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Topic :: Text Processing :: Linguistic',
      ],
      keywords='monitoring information gathering publishing',
      url='https://bitbucket.org/wwsmith/ipf',
      author='Warren Smith',
      author_email='wsmith@tacc.utexas.edu',
      license='Apache',
      packages=find_packages(),
      install_requires=[
        'mtk',
      ],
      include_package_data=True,
      zip_safe=False)
