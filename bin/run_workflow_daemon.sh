#!/bin/sh -l

# get the path to the IPF directory using the location of this cript
IPF_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"

. $IPF_DIR/libexec/env.sh

$PYTHON $IPF_DIR/libexec/run_workflow_daemon.py $@ >& /dev/null
