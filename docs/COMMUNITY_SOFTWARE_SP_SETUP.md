ipf-xsede %VER%-%REL%
# Community Software Advanced Software Publishing Instructions

The COMMUNITY_SOFTWARE_PROVIDER.md document describes how to configure an IPF
workflow to publish a set of available software with a default Support Contact
field.

You may in fact have different sets of available software with different default Support Contacts.  It is possible, assuming that they are organized in a compatible way, to define multiple IPF workflows to publish these sets of software,
giving each set its own default Support Contact.

The main requirement is that each set of Modules that is to have a given Support contact must be organized in its own directory tree.  If it is, we can use the MODULEPATH environment variable to constrain each instance of a software publishing workflow to a given set of modules.  If your modules that require different support contacts are intermixed within a single directory tree, you will have to manually enter the support contact field in each, individually.

To set up multiple workflows to publish software sets with different default Support Contacts, you will essentially be making copies of the workflow that was configured when you ran ipf_configure_xsede, and modifying them slightly.

You should, after having run ipf_configure_xsede, have, in $IPF_ETC_PATH/workflow/glue2/ a RESOURCE_extmodules.json and a RESOURCE_extmodules_periodic.json file.  These are the files that tell IPF the specific parameters for your software
publishing workflow, and how often to run it, respectively.
You will need to make a copy of these two files for each set of software modules that will need its own default Support Contact.

The other file you will need to be aware of (and make copies of) is found in $IPF_ETC_PATH/init.d  It is called ipf-RESOURCE-glue2-extmodules.  This file defines the environment in which the workflow is run, which is important in this instance, as we will be supplying a different MODULEPATH environment variable to each workflow.  If you had MODULEPATH set when you ran ipf_configure_xsede, this file should contain a matching MODULEPATH setting.

The steps to defining multiple software publishing workflows:
*make a copy of $IPF_ETC_PATH/workflow/glue2/RESOURCE_extmodules.json, in the same directory.  You can name it whatever you'd like, but we will stick with RESOURCE_extmodules_sc1.json for this document.

*edit RESOURCE_extmodules_sc1.json, changing the "default_support_contact": field to the new value for this set of software

*make a copy of $IPF_ETC_PATH/workflow/glue2/RESOURCE_extmodules_periodic.json, in the same directory.  Name it by the same convention as above, RESOURCE_extmodules_sc1_periodic.json

*edit the RESOURCE_extmodules_sc1_periodic.json file, changing the "workflow" field from "glue2/RESOURCE_extmodules.json" to "glue2/RESOURCE_extmodules_sc1.json

*make a copy of $IPF_ETC_PATH/init.d/ipf-RESOURCE-glue2-extmodules, calling it ipf-RESOURCE-glue2-extmodules-sc1

*edit the ipf-RESOURCE-glue2-extmodules-sc1 file, changing the MODULEPATH variable to the correct MODULEPATH for the set of modules that have this Support Contact.

The last step is to copy the ipf-RESOURCE-glue2-extmodules-sc1 file to the appropriate system directory (typically /etc/init.d).  You may need to perform a 'chkconfig --add' or equivalent.


