# ipf-xsede %VER%-%REL%
# Community Software Publishing Instructions  
## What is Community Software?


## Why Publish Community Software?

## How to Publish Community Software

The *Information Publishing Framework* "IPF" is a tool used by resource operators to publish dynamic
HPC, HTC, Visualization, Storage, or Cloud resource information to XSEDE's Information Services in a
[GLUE2 standard format](https://www.ogf.org/documents/GFD.147.pdf).
IPF can publish four types of resource information:
 1. Command line software modules 
 2. Batch system configuration and queue contents
 3. Batch scheduler job events
 4. Remotely accessible network services

XSEDE requires Level 1, 2, and 3 operators to publish this dynamic resource information using IPF.
It is also avaialble to campuses and other resource operators who would like to publish dynamic
information to XSEDE information services for use by local services, portals, or gateways. 
IPF complements XSEDE's Resource Description Repository "RDR" which is used to maintain
static resource information. 

The canonical source code repository for IPF can be found at [https://github.com/XSEDE/ipf](https://github.com/XSEDE/ipf.).

This document describes how to install and configure IPF.

### Pre-requisites
- zzzzzzzzzzzfiles must be readable.

### Registering a Support Organization
- zzzzzzzzzzzzzefinition files must be readable, and in a (flat) services directory.

### Preparing Module Files
- zzzzzzzzzzzzzzne programs of your batch scheduler must be executable.

### Requesting that SPs publish your Module Files
- The batch scheduler log file or directory must be readable on the server where IPF is running and by the user running IPF.
- The batch scheduler must be logging at the right level of detail for the IPF code to be able to parse the events.  See the section: Configuring Torque Logging.

### Verying that your software has been published
