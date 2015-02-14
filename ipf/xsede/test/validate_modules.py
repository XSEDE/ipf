#!/usr/bin/env python

import json
import optparse

from validate import validate, elementExists

if __name__ == "__main__":
    doc = validate()

    elementExists("ApplicationEnvironment",doc)
    elementExists("ApplicationHandle",doc)

    print("run 'module avail' or similar and verify that the following information is correct:")
    environments = doc["ApplicationEnvironment"]
    print("  %d application environments" % len(environments))

    print("compare the information in the JSON file to the detailed job information from 'module avail' and 'module show'")
