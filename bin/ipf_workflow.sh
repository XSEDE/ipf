#!/bin/bash -l

# loading the login environment so that module commands work

# this script is used for testing

# set up the environment needed to run the workflows
module load teragrid-basic


export PYTHONPATH=$HOME/mtk:$HOME/ipf:.

BIN_DIR=`dirname $0`

# edit ipf_workflow if a different python needs to be used
${BIN_DIR}/ipf_workflow $@
