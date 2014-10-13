#!/usr/bin/env python

import json
import optparse

from validate import validate, elementExists

if __name__ == "__main__":
    doc = validate()
    elementExists("ComputingActivity",doc)

    print("run 'qstat' or similar to verify that the following information is correct:")
    activities = doc["ComputingActivity"]
    print("  %d computing activities" % len(activities))
    running = filter(lambda act: "ipf:running" in act["State"],activities)
    print("    %d of them are running" % len(running))
    pending = filter(lambda act: "ipf:pending" in act["State"],activities)
    print("    %d of them are pending" % len(pending))
    held = filter(lambda act: "ipf:held" in act["State"],activities)
    print("    %d of them are held" % len(held))

    print("compare the job descriptions in the JSON file to the detailed job information from 'qstat -f' or similar")
