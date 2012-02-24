#!/bin/bash

module load python

export GLUE2_HOME=$HOME/glue2

export PYTHONPATH=$GLUE2_HOME/lib

$GLUE2_HOME/libexec/subscribe.py
