ipf-xsede %VER%-%REL%
# Community Software Area (CSA) Software Publishing Instructions

In a typical IPF installation, the Service Provider (SP) configures an extmodules workflow to publish about software
the SP supports. This workflow uses the Modules or LMod files a system, possibly customized with some extra fields,
to publish information about software that is available and supported. As a convenience, IPF allows the SP to define
a default Support Contact for an extmodules workflow that is added to all the software that doesn't have its own
Support Contact defined.

This document covers how to create additional extmodule workflows for publishing software modules supported by other
organizations, like Community Software Providers. This additional extmodules workflow can be configured with a different
default Support Contact than the primary exdmodules workflow that lists the SP (or XSEDE) as the Support Contact.

The main requirement is that the Modules that will use a given Support Contact must be organized in their own directory tree.
If it is, we can use the MODULEPATH environment variable to constrain each instance of a software publishing workflow to a
given set of modules.  If your modules that require different support contacts are intermixed within a single directory tree,
you will have to manually enter the Support Contact field in each module file individually.

This document assumes that you have already defined an extmodules workflow using the instructions from IPF's INSTALL.md.

To set up additional workflows to publish software sets with different default Support Contacts, you will essentially be
making copies of the workflow that was configured when you ran ipf_configure_xsede, and modifying them slightly.

You should, after having run ipf_configure_xsede, have, in $IPF_ETC_PATH/workflow/glue2/ a RESOURCE_extmodules.json and
a RESOURCE_extmodules_periodic.json file. These are the files that tell IPF the specific parameters for your software
publishing workflow, and how often to run it, respectively. You will need to make a copy of these two files for each set
of software modules that will need its own default Support Contact.

The other file you will need to be aware of (and make copies of) is ipf-RESOURCE-glue2-extmodules under $IPF_ETC_PATH/init.d.
This file defines the environment in which the workflow is run, which is important in this instance, as we will be supplying
a different MODULEPATH environment variable to each workflow. If you had MODULEPATH set when you ran ipf_configure_xsede,
this file should contain a matching MODULEPATH setting.

The steps to defining additional software publishing workflows:

## 1) Create a new workflow config, with default Support Contact
* Make a copy of $IPF_ETC_PATH/workflow/glue2/RESOURCE_extmodules.json, in the same directory.  You can name it whatever
you'd like, but we will stick with RESOURCE_extmodules_sc1.json for this document.

* Edit RESOURCE_extmodules_sc1.json, changing the "default_support_contact": field to the new value for this set of software

## 2) Create a new matching periodic workflow config
* Make a copy of $IPF_ETC_PATH/workflow/glue2/RESOURCE_extmodules_periodic.json, in the same directory.  Name it by the
same convention as above, RESOURCE_extmodules_sc1_periodic.json

* Edit the RESOURCE_extmodules_sc1_periodic.json file, changing the "workflow" field from "glue2/RESOURCE_extmodules.json"
to "glue2/RESOURCE_extmodules_sc1.json

## 3) Create a new workflow init.d entry, with the proper MODULEPATH
* Make a copy of $IPF_ETC_PATH/init.d/ipf-RESOURCE-glue2-extmodules, calling it ipf-RESOURCE-glue2-extmodules-sc1

* Edit the ipf-RESOURCE-glue2-extmodules-sc1 file, changing the MODULEPATH variable to the correct MODULEPATH for the set
of modules that have this Support Contact.

* Finally copy the ipf-RESOURCE-glue2-extmodules-sc1 file to the appropriate system directory (typically /etc/init.d).
You may need to perform a 'chkconfig --add' or equivalent.
