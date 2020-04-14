# ipf-xsede %VER%-%REL%
# Community Software Publishing Instructions  
## What is Community Software?

Software on XSEDE resources falls into three categories based on who installs it and on who the intended
users are:
1. XSEDE Service Provider "SP" installed software intended **for resource projects and users**
2. XSEDE allocated project installed software and applications **for private project use**
3. XSEDE allocated project installed software and applications **shared with other projects and users**

So that current and prospective users can discover software that SPs install for their use (the first category above), SPs
publish information about their software using the XSEDE provided *Information Publishing Framework* (IPF) tool which
reads information from software modules that have both environment setup information and descriptive information. This
design makes it easier for SPs to maintain software information for each component in a single file. IPF reads descriptive
information in modules and publishes to XSEDE's Information Services, which makes the information available thru public
APIs to the User Portal, the Research Software Portal, Science Gateways, and other services. These services are then
able to create software discovery interfaces.

XSEDE allocated Level 1 and 2 service provides are required to use IPF to publish user facing information , however IPF
is available to both allocated and unallocated SPs including Level 1, 2, 3, and Campus SPs.

This documentation explains how an XSEDE allocated project installing software on XSEDE resources to share with other
projects and users of that resource, as described in the third category above, can also use the IPF tool already installed by
the SPs to publish information about their shared software. The types of XSEDE allocated projects that will most benefit
from this feature are community software developers/providers and science gateways.

## Why Publish Community Software?

Current and prospective XSEDE users can discover software on XSEDE resources using the
User Portal [Comprehensive Software Search](https://portal.xsede.org/software#/) and the
Research Software Portal [Software Discovery Interface](https://software.xsede.org/search-resources).

If community software developers/providers and science gateways publish information about the software they install
on XSEDE resources, other projects and users will be able to more easily discover it thru XSEDE provided software
discovery interfaces and also use that software.

Community software providers and science gateways can also use the same XSEDE APIs that the User Portal and
Research Software Portlal use to access information about the software that they or other community software provides
install on XSEDE resources.

## How to Publish Community Software

To publish information about community software on XSEDE resources the project installing it will need to:
 1. Obtain a Community Software Area "CSA" (i.e. a directory) on the XSEDE resources they want to install software on
 2. Register their Community Software Support Organization contact informatiion
 3. Install software in Community Software Areas on resources
 4. Define modules with software environment setup details and descriptive information that IPF can publish
 5. Request that SPs publish their community software module descriptions using their SP operated IPF

### Obtain a Community Software Area (CSA)

A CSA gives projects a share space where multiple people can install and maintain software that is outside of a single users
home directory and thus not dependent on a single user. A CSA is strongly recommended because it is a bad security practice
and against policy for users to give other users write access to anything inside their home directory. A CSA is the only way for
multiple members of a project to share software install and support responsibilities.

The list of XSEDE SP resources that support CSAs is [here](https://info.xsede.org/wh1/warehouse-views/v1/resources-csa/).
Before requesting a new CSA please review the details the SP has listed under *CSA Feature Description*. If you are a Science
Gateway you should also review informaiton in *Gateway Recommended Use*. If you wish to install and share software on an
XSEDE resource that is not listed, contact the SP thru help@xsede.org requesting that they support the XSEDE Community
Sofware Area feature.

To request a CSA follow [these instructions](https://www.xsede.org/ecosystem/software). Send separate e-mail requests when
requesting multiple CSAs.

### Register a Community Software Support Contact

By installing shared software you must provide front line support for that software, even if you get the software from a third
party. How you provide that front line support is up to you, so you can coordinate with the software provider or other support
resources that you have access to.

To provide software support in the XSEDE environment you need to register your support contact details. XSEDE maintains
a list of registered support contacts [here](https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/). If your contact details 
are not listed, register them by e-mailing help@xsede.org with the Subject *"Register new RSP Support Contact"* providing
your project or support organization name and listing one or more methods users can use to contact you, such as a web URL,
an e-mail address, and/or a phone number.

Once your support contacts appear on the registered support contacts list, click on the *Contact Detail Link* and copy the
Contact Metadata URL in the detail view. You will need to embed this URL in each of your software modules.

### Install Software in Community Software Areas of resources

There are a few basic contraints on software installed in a Community Software Area:
 1. Software must not require root to install or use
 2. You must have the proper licenses to install and share it
 3. Using the sofware must not violate [XSEDE's acceptable use policies](https://www.xsede.org/ecosystem/operations/usagepolicy)
 4. You may only run persitent services from that software as approved by the SP
 
Make sure you also review and comply with any constrainst spelled out by the SP in their *CSA Feature Description*.

Install and organize software in your Community Software Area as you see fit.

### Define software modules

Each software component that you wish to publish about needs a module file in the modules/ sub-directory of your CSA.

Instructions on what fields to place in the Module are in the *Best Practices for Software publishing  (Modules Files)* section
of the acompanying IPF INSTALL documentation. Note that the SupportContact field should have the URL that points to
the appropriate support organization metadata, which is the URL you copied above.

### Request that SPs publish your software modules

Send separate e-mail requests to help@xsede.org for each SP resource that has a CSA with modules that you want to publish.
In your request(s) includes the full path (pwd) to the directory with your modules and the support organization metadata URL
you copied above. SPs will configure IPF to ensure that all your software modules reference your SupportContact information.

### Verifying that your software is discoverable

After the SP tells you that they are publishing your software module information you should be able to discover your software
in the Research Software Portal [here](https://software.xsede.org/search-resources).

## Additionl Resources
The IPF source is available at [https://github.com/XSEDE/ipf](https://github.com/XSEDE/ipf.).
