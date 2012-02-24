#!/bin/bash

module load python

export GLUE2_HOME=%INSTALL_DIR%
export PYTHONPATH=$GLUE2_HOME/lib

$GLUE2_HOME/libexec/glue2_tacc_sge.py
