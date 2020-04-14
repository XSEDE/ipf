# ipf-xsede %VER%-%REL%
# Community Software Publishing Instructions  
## What is Community Software?

Software on XSEDE resources may be grouped into three categories based on who installs it and on who its intended
users are:
1. XSEDE Service Provider "SP" installed software intended for **resource users**
2. XSEDE allocated project installed software (often appliations) for **personal project use**
3. XSEDE allocated project installed software instended for sharing with **other resource users**

XSEDE SPs publishing descriptive information about the first category of software so that users can discover it from
the User Portal, the Research Software Portal, and potentially others services like Science Gateways. XSEDE provides
SPs the *Information Publishing Framework* (IPF) software to automate publishing information in SP maintained software
module so that SPs can maintain sofware environment setup recipes and software descriptions in a single file.

XSEDE allocated Level 1 and 2 service provides are required to publish their software information using IPF, however IPF
is available to allocated and unallocated SPs including Level 1, 2, 3, and Campus SPs. Information published using IPF
is aggregated in XSEDE's Information Services and made available thru public APIs to the User Portal, the Research
Software Portal, Science Gateways, and other services.

This documentation explains how an XSEDE allocated project installing software on XSEDE resources for sharing with other
resource users, as described in the third category above, can use the IPF tool already installed by the service providers to
publish information about their software. XSEDE allocated Science Gateways and community software developers/providers
will find this capability most useful.

## Why Publish Community Software?

The XSEDE User Portal [Comprehensive Software Search](https://portal.xsede.org/software#/) and the
[Research Software Portal Software Discovery Interface](https://software.xsede.org/search-resources) help users
discover software on XSEDE resources. By publishing information about community installed software on XSEDE
resources XSEDE uses will be able to more easily discover and use that software.

## How to Publish Community Software

To publish information about community software on XSEDE resources the group installing and maintaining it will need to:
 1. Obtain a Community Software Area "CSA" (i.e. a directory) on the XSEDE resources where they want to install their software
 2. Register themselves as a Community Software Support Organization
 3. Install software in Community Software Areas on resources
 4. Define modules with software environment setup details and software descriptions that IPF can publish
 5. Request that SPs publish their community software module descriptions using their SP installed IPF

### Obtain a Community Software Area

Not all XSEDE SPs support installing and sharing community software. Which SPs support Community Software Areas is 
[here](http://info.xsede.org/wh1/warehouse-views/v1/resources-csa/). Before requesting a new Community Software Area please
review any details the SP las listed under *CSA Feature Description*. If you are a Science Gateway you should also review the
informaiton in *Gateway Recommended Use*. If you wish to install and share software on an XSEDE resource that is not listed,
contact the SP thru help@xsede.org requesting that they start supporting XSEDE Community Sofware Areas.

To request a Community Software Area follow [these instructions](https://www.xsede.org/ecosystem/software). A Community
Software Area gives you a space outside of a single users home directory where multiple users can install and maintain the
software. This is important because it is bad security practice and against policy for one user to give other users the ability
to write or update files in their home directory.

### Register a Community Software Support Contact

By installing shared software you must provide front line support for that software, even if you get the software from a third
party. You can provide that front line support using the software provider or other support resources as you see fit.

To provide software support in the XSEDE environment you need to register your support contact details. XSEDE maintains
a list of registered support contacts [here](https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/). If your contact deails 
aren't listed, register them by e-mailing help@xsede.org with the Subject *"Register new RSP Support Organization"* and
provide the project or support organization name and list the methods users can use to contact you, including a web URL,
an e-mail address, and/or a phone number.

Once your support contacts appear on the registered support contacts list, click on the *Contact Detail Link* and copy the
Contact Metadata URL in the detail view. You will need to embed this URL in each of your software modules.

### Install Software in Community Software Areas of resources

There are a few basic contraints on software installed in Community Software Areas:
 1. Software must not require root to install or use
 2. You must have the proper licenses to install and share it
 3. You may only run persitent services from that software once approved by the SP

Install and organize software in your Community Software Area.

### Define software modules

Each software component that you wish to publish about needs a module file in the modules/ sub-directory of your CSA.

Instructions on what fields to place in the Module are in the acompanying IPF INSTALL documentation
*Best Practices for Software publishing  (Modules Files)* section. Note that SupportContact field should have
the URL that points to the appropriate support organization metadata, which is the URL you copied above.

### Request that SPs publish your software modules

E-mail help@xsede.org each of the SPs for you CSAs requesting that they publish your CSA modules. In your request
includes the full path (pwd) to the directory with your modules.

### Verifying that your software is discoverable
After the SP tells you that they are publishing your software module information you should be able to discover your software
in the Research Software Portal here:
* https://software.xsede.org/search-resources

## Additionl Resources
- IPF source can be found at [https://github.com/XSEDE/ipf](https://github.com/XSEDE/ipf.).
