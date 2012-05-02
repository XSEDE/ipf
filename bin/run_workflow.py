#!/usr/bin/env python

import sys

from ipf.engine import WorkflowEngine

#######################################################################################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: run_workflow.py <workflow file>")
        sys.exit(1)

    engine = WorkflowEngine()
    engine.run(sys.argv[1])
