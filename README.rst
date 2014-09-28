
Overview
--------

The Information Publishing Framework (IPF) is a generic framework for gathering and publishing
information. This project is narrowly focused on those topics and does not include mechanisms to analyze or
visualize information. IPF grew out of work to publish information about TeraGrid compute resources according
to the [GLUE 2 specification](http://www.ogf.org/documents/GFD.147.pdf) and that continues to be one of the
main goals of this project.

IPF gathers and publishes information using simple workflows. These workflows are defined using JSON (see the
etc/workflows directory) and steps in the workflows are implemented as Python classes. Each step in the
workflow can require input Data, can produce output Data, and can publish Representations of Data. A typical
workflow consists of a number of information gathering steps and a few steps that publish Representations to
files or to remote services (e.g. REST, messaging).

Workflow steps specify what Data they require and what Data they produce. This allows IPF to construct
workflows based on partial information - in the case where there are not steps that produce the same Data, an
entire workflow can be constructed from a single publish step and its required input Data. At the other
extreme, workflows can be exactly specified with specific steps identified and the outputs of steps bound to
the inputs of other steps. A typical workflow (e.g. GLUE 2) specifies what steps to include but lets IPF
automatically link outputs to inputs of these steps.

Workflows can run to completion relatively quickly or they can continuously run. The first type of workflow
can be used to run a few commands or look at status files and publish that information. The second type of
workflow can be used to monitor log files and publish entries written to those files. Workflows are typically
run periodically as cron jobs.  The program libexec/run_workflow.py is for executing workflows that complete
quickly and the program libexec/run_workflow_daemon.py is used to manage long-running workflows. The daemon


License
----------

This software is licensed under Version 2.0 of the Apache License.

Installation
--------------

This software can be configured using pip, setuptools, or if you are participating in `XSEDE <http://www.xsede.org>`_, via RPM packages.

pip Installation
-------------------

You may need to install `pip` on your system. There is a package named `python-pip` that a system administrator can install or you can install it as a normal user by downloading and running the `get-pip.py <http://pip.readthedocs.org/en/latest/installing.html>`_ script.

If you are not a system administrator or you wish to install this software outside of the shared Python directories, you may wish to create a Python `virtual environment <http://virtualenv.readthedocs.org/en/latest/>`_. Don't forget to add the virtual environment to your shell environment before running pip.

To install via `pip`, you may need to install simply execute:

    $ pip install ipf

easy_install Installation
-------------------------------

You can also install IPF via `easy_install` by:

    $ easy_install ipf

Contact Information
--------------------------

This software is maintained by `Warren Smith <https://bitbucket.org/wwsmith>`_ and you can contact him on bitbucket via a message. If you have problems with this software you are welcome to submit an `issue <https://bitbucket.org/wwsmith/ipf/issues>`_.

Acknowledgements
----------------

This work was supported by the TeraGrid, XSEDE, and FutureGrid projects under National Science Foundation
grants 0503697, 1053575, and 0910812.
