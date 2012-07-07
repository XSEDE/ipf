#!/usr/bin/env python

import sys

min_version = (2,6)
max_version = (2,9)

if sys.version_info < min_version or sys.version_info > max_version:
    print(stderr,"Python version 2.6 or 2.7 is required")
    sys.exit(1)

from ipf.engine import WorkflowEngine

#######################################################################################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: run_workflow.py <workflow file>")
        sys.exit(1)

    engine = WorkflowEngine()
    engine.run(sys.argv[1])
