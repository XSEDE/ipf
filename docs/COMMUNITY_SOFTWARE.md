# ipf-xsede %VER%-%REL%
# Community Software Publishing Instructions  
## What is Community Software?

The software on XSEDE resources can be grouped into three categories based on who install it and on who the
target users of the software are:
1. XSEDE Service Provider "SP" installed software made available to **resource users**
2. XSEDE allocated project installed software for **personal project use**, most often applications
3. XSEDE allocated project installed software made available to **other resource users**

XSEDE SPs publishing descriptive information about the first category of software in order to enable users to discover
that software from the User Portal, the Research Software Portal, and potentially others services like Science Gateways.
XSEDE provides SPs the *Information Publishing Framework* (IPF) tool to automate publishing information in software
module files so that SPs only have to maintain software information in one place.

XSEDE allocated Level 1 and 2 service provides are required to publish software information using IPF, however IPF is
available to both allocated and unallocated SPs including Level 1, 2, 3, and Campus SPs. Information published using
IPF is aggregated in XSEDE's Information Services and made available thru public APIs to the User Portal, the Research
Software Portal, Science Gateways, and other services.

This documentation explains how an XSEDE allocated project that installs and maintains software on XSEDE resources,
as described in the third category above, can also use the IPF tool already installed by the service providers to publish
information about their software. XSEDE allocated projects that will find this capability most useful include Science
Gateways and community software developers/providers.

## Why Publish Community Software?

The XSEDE User Portal [Comprehensive Software Search](https://portal.xsede.org/software#/) and the
[Research Software Portal Software Discovery Interface](https://software.xsede.org/search-resources) enable users to
discover software on XSEDE resources. By publishing information about community installed software on XSEDE resources 
XSEDE uses will be able to more easily discover and use that software.

## How to Publish Community Software

Community software providers that want to publish information about their software on XSEDE resources will need to:
 1. Obtain a Community Software Area  "CSA" (i.e. directory) on the XSEDE resources where they can install their software
 2. Register the organization support the community software
 3. Install their software into the Community Software Area
 4. Define modules users can use to access the software that contain the information IPF will publish
 5. Request that SPs publish their community software module information using the SP installed IPF

### Obtain a Community Software Area

To request a Community Software Area follow [these instructions](https://www.xsede.org/ecosystem/software).

### Register the organization support the community software

Browse already registered support organizations in the [Research Software Portal](https://software.xsede.org/support-organizations),
and if needed follow the instructions on that page to register a new organization.

Once you have a registered organization copy the URL to the support organization metadata which should
have the form:
- https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/globalid/<standard_name>

This URL will be used in softwre modules below so that each module contains upport organizatio informatiaon.

### Install their software into the Community Software Area

There are a few basic contraints on Community Software Areas use:
 1. Software must not require root to install or use
 2. You must have the proper licenses to install and share it
 3. You may only run persitent services from that software once approved by the SP

Install and organize software in your Community Software Area.

### Define software modules

Each software component that you wish to advertise about needs a module file under the modules/ sub-directory of your CSA

Instructions on what fields to place in the Module are in the acompanying IPF INSTALL documentation
*Best Practices for Software publishing  (Modules Files)* section. Note that SupportContact field should have
a URL that points to the appropriate support organization metadata. This is the URL you copied above.

### Request that SPs publish your software modules

E-mail help@xsede.org requesting that the adminsitrators of the resource(s) with your CSA publish your modules. Make sure you request
includes the path to the directory where you placed your module files.

### Verifying that your software is discoverable
After the SP tells you that they are publishing your software module information you should be able to discover thru the
Research Software Portal's here:
* https://software.xsede.org/search-resources

## Additionl Resources
- IPF can be found at [https://github.com/XSEDE/ipf](https://github.com/XSEDE/ipf.).
