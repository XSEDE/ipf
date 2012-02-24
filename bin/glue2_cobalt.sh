#!/bin/bash

export GLUE2_HOME=%INSTALL_DIR%
export PYTHONPATH=$GLUE2_HOME/lib

$GLUE2_HOME/libexec/glue2_cobalt.py
