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
    running = [act for act in activities if "ipf:running" in act["State"]]
    print("    %d of them are running" % len(running))
    pending = [act for act in activities if "ipf:pending" in act["State"]]
    print("    %d of them are pending" % len(pending))
    held = [act for act in activities if "ipf:held" in act["State"]]
    print("    %d of them are held" % len(held))

    print("compare the job descriptions in the JSON file to the detailed job information from 'qstat -f' or similar")
