#!/bin/sh -l

# get the path to the IPF directory using the location of this cript
IPF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"

. $IPF_DIR/libexec/env.sh

filename=$(basename $1)
base=${filename%.*}

$PYTHON $IPF_DIR/libexec/run_workflow_cron.py $@ >> $IPF_DIR/var/$base.log 2>&1
