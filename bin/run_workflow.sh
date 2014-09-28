#!/bin/sh -l


# python 2.6 or 2.7 is required

# so may need to load a module:
#module load python

# or specify a specific python executable:
#PYTHON=python2.6
PYTHON=python

# get the path to the IPF directory using the location of this cript
IPF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"

$PYTHON $IPF_DIR/ipf/run_workflow.py $@
