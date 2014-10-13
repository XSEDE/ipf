#!/usr/bin/env python

import json
import optparse

from validate import validate, elementExists

if __name__ == "__main__":
    doc = validate()

    elementExists("ComputingManager",doc)
    elementExists("ComputingService",doc)
    elementExists("ExecutionEnvironment",doc)
    elementExists("Location",doc)
    elementExists("ComputingShare",doc)

    print("run 'qstat' or similar to verify that the following information is correct:")
    shares = doc["ComputingShare"]
    print("  %d computing shares" % len(shares))

    print("compare the information in the JSON file to the detailed job information from 'qstat -Q -f' and 'pbsnodes' or similar")
