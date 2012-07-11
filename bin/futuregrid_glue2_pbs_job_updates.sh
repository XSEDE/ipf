#!/bin/sh

module load torque

export PYTHONPATH=@install_dir@/lib

@python@ -u @install_dir@/libexec/run_workflow_daemon.py @install_dir@/etc/workflow/futuregrid/glue2_pbs_job_updates.json
