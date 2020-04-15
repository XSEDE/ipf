ipf-xsede %VER%-%REL%
# Community Software Advanced Software Publishing Instructions

In a typical IPF installation, the Service Provider configures an extmodules
workflow to publish the set of software that they support.  This workflow uses the Modules or LMod files that are on the system, possibly customized with some extra fields, to discover the software that is available and supported.
As a convenience, IPF allows the Service Provider to define a default Support Contact to be published for any piece of software that lacks its own Support Contact field.

This document covers how to create additional extmodule workflows for publishing software modules supported by other organizations, like Community Software Providers.  Since they are supported by other organizations, their default Support Contact would be different than the software that is supported by the Service Provider.

The main requirement is that each set of Modules that is to have a given Support contact must be organized in its own directory tree.  If it is, we can use the MODULEPATH environment variable to constrain each instance of a software publishing workflow to a given set of modules.  If your modules that require different support contacts are intermixed within a single directory tree, you will have to manually enter the support contact field in each, individually.

This document assumes that you have already defined an extmodules workflow using the instructions from IPF's INSTALL.md.

To set up multiple workflows to publish software sets with different default Support Contacts, you will essentially be making copies of the workflow that was configured when you ran ipf_configure_xsede, and modifying them slightly.

You should, after having run ipf_configure_xsede, have, in $IPF_ETC_PATH/workflow/glue2/ a RESOURCE_extmodules.json and a RESOURCE_extmodules_periodic.json file.  These are the files that tell IPF the specific parameters for your software
publishing workflow, and how often to run it, respectively.
You will need to make a copy of these two files for each set of software modules that will need its own default Support Contact.

The other file you will need to be aware of (and make copies of) is found in $IPF_ETC_PATH/init.d  It is called ipf-RESOURCE-glue2-extmodules.  This file defines the environment in which the workflow is run, which is important in this instance, as we will be supplying a different MODULEPATH environment variable to each workflow.  If you had MODULEPATH set when you ran ipf_configure_xsede, this file should contain a matching MODULEPATH setting.

The steps to defining multiple software publishing workflows:
##Create a new workflow config, with default Support Contact
*make a copy of $IPF_ETC_PATH/workflow/glue2/RESOURCE_extmodules.json, in the same directory.  You can name it whatever you'd like, but we will stick with RESOURCE_extmodules_sc1.json for this document.

*edit RESOURCE_extmodules_sc1.json, changing the "default_support_contact": field to the new value for this set of software

##Create a new matching periodic workflow config
*make a copy of $IPF_ETC_PATH/workflow/glue2/RESOURCE_extmodules_periodic.json, in the same directory.  Name it by the same convention as above, RESOURCE_extmodules_sc1_periodic.json

*edit the RESOURCE_extmodules_sc1_periodic.json file, changing the "workflow" field from "glue2/RESOURCE_extmodules.json" to "glue2/RESOURCE_extmodules_sc1.json

##Create a new workflow init.d entry, with the proper MODULEPATH
*make a copy of $IPF_ETC_PATH/init.d/ipf-RESOURCE-glue2-extmodules, calling it ipf-RESOURCE-glue2-extmodules-sc1

*edit the ipf-RESOURCE-glue2-extmodules-sc1 file, changing the MODULEPATH variable to the correct MODULEPATH for the set of modules that have this Support Contact.

The last step is to copy the ipf-RESOURCE-glue2-extmodules-sc1 file to the appropriate system directory (typically /etc/init.d).  You may need to perform a 'chkconfig --add' or equivalent.


