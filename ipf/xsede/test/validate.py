#!/usr/bin/env python

import json
import optparse
import os
import sys

import jsonschema # https://github.com/Julian/jsonschema

class MyRefResolver(jsonschema.RefResolver):
    def __init__(self, schema, schema_dir):
        jsonschema.RefResolver.__init__(self,schema.get("id", ""),schema)
        self._schemas = {}
        for file_name in os.listdir(schema_dir):
            if os.path.splitext(file_name)[1] != ".json":
                continue
            #print("loading schema file "+file_name)
            f = open(os.path.join(schema_dir,file_name))
            schema_str = f.read()
            f.close()
            schema = json.loads(schema_str)
            try:
                self._schemas[schema["id"]] = schema
            except KeyError:
                print("  didn't find id in "+file_name)

    def resolve_remote(self, uri):
        try:
            return self._schemas[uri]
        except KeyError:
            print("calling default resolve_remote on "+uri)
            jsonschema.RefResolver.resolve_remote(self,uri)

def validate():
    path = os.path.abspath(__file__)
    path = os.path.split(path)[0]    # drop file name
    schema_dir = os.path.join(path,"JSON","schema")

    parser = optparse.OptionParser("usage: %prog [options] <json file>")
    parser.add_option("-d", "--schema_dir", action="store", type="string", dest="schema_dir", default=schema_dir,
                      help="the local directory containing the GLUE 2 json-schema files")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("wrong number of arguments")

    f = open(os.path.join(options.schema_dir,"Glue2.json"))
    schema_str = f.read()
    f.close()
    f = open(args[0])
    doc_str = f.read()
    f.close()

    schema = json.loads(schema_str)
    doc = json.loads(doc_str)

    jsonschema.validate(doc,schema,resolver=MyRefResolver(schema,options.schema_dir))
    print("Success: document is valid JSON GLUE2")
    return doc

def elementExists(name, doc):
    if name not in doc:
        print("Failure: didn't find %s in document" % name)
        sys.exit(1)
    else:
        print("Success: found %s element" % name)

if __name__ == "__main__":
    validate()
