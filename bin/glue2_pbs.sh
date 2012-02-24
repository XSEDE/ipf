#!/bin/bash

module load python/2.7

export GLUE2_HOME=%INSTALL_DIR%
export PYTHONPATH=$GLUE2_HOME/lib

$GLUE2_HOME/libexec/glue2_pbs.py
