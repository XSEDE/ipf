
XSEDE Tests
===========

This directory contains test programs that can be used as part of XSEDE testing

Setup
-----

Change to this directory:

    $ cd ipf/ipf/xsede/test

Download the current GLUE 2.0 JSON schema:

    $ git clone https://github.com/OGF-GLUE/JSON.git

Download the jsonschema validator:

    $ git clone https://github.com/Julian/jsonschema.git

And include it in your PYTHONPATH:

    $ export PYTHONPATH=$PYTHONPATH:$PWD/jsonschema:.

(Alternatively, you can install the jsonschema validator on your system by running 'pip install jsonschema' or
'yum install python-jsonschema'.)

Testing
-------

To validate a GLUE2 JSON file run:

    $ ./validate.py PATH_TO_DOCUMENT.json

This will produce either a success message or an error.

To sanity check the documents, there are three additional tests:

    $ ./validate_compute.py path/to/compute.json
    $ ./validate_activities.py path/to/activities.json
    $ ./validate_modules.py path/to/apps.json

These scripts check the compute and activities documents output by the xsede/glue2/SCHEDULER_compute.json
workflows and the xsede/glue2/lmod.json or xsede/glue2/modules.json workflow, in that order.
