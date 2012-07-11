#!/bin/sh

module load torque

export PYTHONPATH=@install_dir@/lib

@python@ @install_dir@/libexec/run_workflow.py @install_dir@/etc/workflow/futuregrid/glue2_pbs.json >& @install_dir@/var/futuregrid_glue2_pbs.log
