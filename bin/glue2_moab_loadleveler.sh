#!/bin/bash

export GLUE2_HOME=%INSTALL_DIR%
export PYTHONPATH=$GLUE2_HOME/lib

export PATH=/N/soft/linux-sles9-ppc64/python-2.6.5-64/bin/python:$PATH

$GLUE2_HOME/libexec/glue2_moab_loadleveler.py
