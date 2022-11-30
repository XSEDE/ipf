
# ipf-xsede %VER%-%REL%
# README
## Overview

The Information Publishing Framework (IPF) is a generic framework for gathering and publishing information. IPF
focuses narrowly on gatethering and publishing, and not on analyzing or visualizing information. IPF grew out of
work to publish information about TeraGrid compute resources using the
[GLUE 2 specification](http://www.ogf.org/documents/GFD.147.pdf). IPF continues to support data gathering and
publishing in the ACCESS-CI program which succeeded XSEDE and TeraGrid.

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
run periodically as cron jobs. The program libexec/run_workflow.py is for executing workflows that complete
quickly and the program libexec/run_workflow_daemon.py is used to manage long-running workflows. The daemon

## License

This software is licensed under Version 2.0 of the Apache License.

## Installation

Installation instructions are in [docs/INSTALL.md](docs/INSTALL.md).

## Contact Information

This software is maintained by ACCESS-CI, though its source is still currently found in the XSEDE github organization. [XSEDE](https://www.github.com/XSEDE).  and you can contact the ACCESS-CI helpdesk if you need help using it. 

If you have problems with this software you are welcome to submit an [issue](https://github.com/XSEDE/ipf/issues).

## Acknowledgements

This work was supported by the TeraGrid, XSEDE, FutureGrid, and XSEDE 2 projects under National Science Foundation
grants 0503697, 1053575, 0910812, and 1548562.
