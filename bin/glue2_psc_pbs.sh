#!/bin/bash -l

module load python/2.7.0
module load tgresid

export GLUE2_HOME=%INSTALL_DIR%
export PYTHONPATH=$GLUE2_HOME/lib

$GLUE2_HOME/libexec/glue2_psc_pbs.py
