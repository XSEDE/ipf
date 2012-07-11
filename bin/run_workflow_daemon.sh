#!/bin/sh

export PYTHONPATH=@install_dir@/lib

@python@ -u @install_dir@/libexec/run_workflow_daemon.py $@
