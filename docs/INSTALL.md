# ipf-xsede %VER%-%REL%
# Installation and Configuration Instructions  
## What is IPF?

The *Information Publishing Framework* "IPF" is a tool (1) used by resource operators to publish dynamic
resource information to XSEDE's Information Services (2). IPF can publish four types of resource information:
 1. Software Modules available from the command line
 2. Batch system configuration and queue contents
 3. Network services information
 4. Batch scheduler job events
 
XSEDE requires Level 1, 2, and 3 operators (3) to publish this dynamic resource information using IPF.

IPF complements XSEDE's Resource Description Repository "RDR" (4) which is used to maintain
static resource information. 

Campuses and other research resource operators that are not affiliated with XSEDE are welcome to use IPF
and to publish their resource information to XSEDE Information Service. By doing so, local services, portals,
and gateways can use XSEDE Information Services APIs to access both local resource information and
XSEDE resource information. 

This document describes how to install and configure IPF.

## How does IPF Work?
### What is IPF?

IPF is a Python program that gathers resource information, formats it in a GLUE2 standard format (5),
and publishes it to XSEDE's Information Services. Each type of information that is published has a
"workflow" that defines the steps that IPF executes to discover, format, and publish the information.

### How is an IPF workflow defined?
Each IPF workflow consists of a series of "steps" that can have inputs, outputs, and dependencies.
The steps for each workflow are defined in one or more JSON formatted files. Workflow JSON files
can incorporate other workflow JSON files: for example, the `<resource>_services_periodic.json`
workflow contains one step, which is the `<resource>_services.json` workflow.

IPF workflows are typically defined by JSON files under $IPF_ETC/ipf/workflow/, particularly in
$IPF_ETC/ipf/workflow/glue2.  

### How is an IPF workflow invoked?
To run a workflow execute the ipf_workflow program passing it a workflow definition file argument,
like this:

    $INSTALL_DIR/ipf-VERSION/ipf/bin/ipf_workflow <workflow.json>

Workflow JSON files are specified relative to $IPF_ETC, so `ipf_workflow sysinfo.json`
and `ipf_workflow glue2/<resource>_services.json` are both valid invokations.

Scripts for init.d are provided by ipf_configure_xsede for each workflow it configures.
The init.d scripts can be found in $IPF_ETC/ipf/init.d.  Each script runs one workflow,
on a periodic basis, and are typically copied into the system /etc/init.d directory as part of the
installation process.

### Which workflows should I configure and run?
The following workflows are recommended for the listed scenarios.

Software Module workflow: required for all Level 1, 2 and 3 *SPs that offer login and batch computing*

Batch System workflow (compute workflow): required for all Level 1, 2, and 3 *SPs that offer batch computing*

Network Accessible Services workflow: recommended for all Level 1, 2, and 3 *SPs that operate OpenSSH or GridFTP services*

Batch Scheduler Job Event workflow (activity workflow): recommended for all Level 1 and 2 *SPs that offer XSEDE allocated batch computing*

## Pre-requisites

### Software Modules workflow requirements
- The module or Lmod files must be readable.

### Batch System workflow requirements 
- The command line programs for your batch scheduler must be executable.

### Network Services workflow requirements
- The service definition files must be readable, and in a single directory.

### Batch Scheduler Job Events workflow requirements
- The batch scheduler log file or directory must be readable on the server where IPF is running and by the user running IPF.
- The batch scheduler must be logging at the right level of detail for the IPF code to be able to parse the events.  See the section: Configuring Torque Logging.

## Preparing for Install IPF

- Before installing IPF operators should register their resource in RDR (4).
- Install and run IPF on a single server for each resource.
- If IPF will authenticate to Information Services using a X.509 host key/certificate, the public and private keys must be readable by the user running IPF.
- To install IPF on machines that are part of multiple XSEDE resources please first review [XSEDE's Advanced Integration Options](https://www.ideals.illinois.edu/bitstream/handle/2142/99081/XSEDE_SP_Advanced_Integration_Options.pdf) documentation.
- If you already have an older IPF create a backup of the /etc/ipf working configurations:

    $ tar -cf ipf-etc-yyyymmdd.tar /etc/ipf

### Software Dependencies

- Python 3.6 or newer
- The python-amqp package, version between 1.4.0 and 1.4.9
- The python-setuptools package IF installing by RPM.
- (Optional) The xdresourceid tool. If not available a resourceid will need to be configured by hand.

*These dependencies are encoded in the RPM.*

## Installing IPF
There are two recommended ways to install IPF: you can use pip install, or you can install from the XSEDE RPMs on software.xsede.org.

Installing IPF from RPMs will put it in the directories /usr/lib/python-`<VERSION>`/site-packages/ipf, /etc/ipf, /var/ipf).

To install to an alternate location we recommend using pip.

### Pip installation

To install using pip, you need to have the pip package installed in an appropriate version of Python (3.6+).
We recommend using venv to manage Python installations.  More information on venv is available at 
[https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

Once you have a Python 3.6 environment (whether venv or not), to install execute:

    $ pip install ipf

When installing via pip:  unlike in an RPM install, the files get installed relative to your Python installation (whether in a virtualenv or system Python).
Notably, ipf_configure_xsede and ipf_workflow end up in the virtualenv's bin directory,
and the location IPF expects to find as its IPF_ETC_PATH (/etc/ipf in an RPM install) is relative to the Python site-packages directory.

You can find your site-packages path for the Python you used for the pip install with: 
$ python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])'

When running any IPF commands by hand in a pip install, you will need to set the environment variable IPF_ETC_PATH.
Its value should be the site-packages directory referenced above, plus "/etc/ipf".  For a system Python, this might look something
like "/usr/lib/python3.6/site-packages/etc/ipf". If you have run ipf_configure_xsede to set up your workflows, and chosen the recommended
base directory, your workflow definitions will have the appropriate IPF_ETC_PATH defined in them.

### RPM Installation

Note(s):
 - The RPM will automatically create an "xdinfo" account that will own the install and that will execute the workflows via sudo.

Steps:
1) Configure XSEDE RPM repository trust
For a production version use [Production Repo Trust Instructions](https://software.xsede.org/production/repo/repoconfig.txt)
For a development/testing version use [Development Repo Trust Instructions](https://software.xsede.org/development/repo/repoconfig.txt)

2) Install ipf-xsede

    $ yum install ipf-xsede

### tar.gz Installation

Installing from the tar.gz is no longer recommended.  It will still work, but we recommend using venv and pip to install to alternate locations, and/or development versions.

Note(s):
- If you need to install development versions, replace the URL prefixes 'http://software.xsede.org/production' with 'http://software.xsede.org/development' in the instructions below.

Steps:
1) Create a normal user to run this software
   The recommended username 'xdinfo', but you can use a different one

2) Install the Python amqp package. It MUST be at least version 1.4.0, and must have major version of 1 (2.0 and above will not work).  We recommend amqp 1.4.9.
    You can 'yum install python-amqp', 'pip install amqp' (into the default location or into a Python virtualenv) or you can install from a "wheel" download from pypi. You may need to do this as root, depending on the install directory (e.g. /opt/). These files need to be readable by the user you created in step 1).
   a) Look at the files from https://pypi.org/project/amqp/1.4.9/#files/
	specifically, download:
https://files.pythonhosted.org/packages/ed/09/314d2788aba0aa91f2578071a6484f87a615172a98c309c2aad3433da90b/amqp-1.4.9-py2.py3-none-any.whl

   b) pip install -install-option="-prefix=$PREFIX_PATH" amqp-1.4.9-py2.py3-none-any.whl
     (where $PREFIX_PATH is your AMQP_PATH, i.e. the place you want to install the amqp lib)

3) Install the XSEDE version of the Information Publishing Framework (ipf-xsede):
   a) Download the .tgz file from http://software.xsede.org/production/ipf/ipf-xsede/latest/
   b) Untar this file into your install directory. The result will be a directory hierarchy under

    $ INSTALL_DIR/ipf-VERSION.

4) As the user created in step 1), configure the ipf_workflow script in $ INSTALL_DIR/ipf-VERSION/ipf/bin
   a) Set PYTHON to be name of (or the full path to) the Python interpreter you wish to use
   b) If you installed Python amqp into a non-default location, set AMQP_PATH to be the path where you installed it and uncomment this line and the following line that sets PYTHONPATH
   c) Run '$INSTALL_DIR/ipf-VERSION/ipf/bin/ipf_workflow sysinfo.json'. The workflow steps should run, but you may see failures related to host and/or site names.

## Updating a previous IPF installation

The JSON files that have been written by previous runs of ipf_configure_xsede would, in some previous versions of IPF get overwritten by subsequent runs of ipf_configure_xsede.  This is no longer the case--previous versions get backed up, not overwritten.  They will _not_ be erased by removing OR updating the package (nor will the service files copied to /etc/init.d be erased). 

To perform the update to the latest RPM distribution of ipf-xsede:

 1. $ sudo yum update ipf-xsede
 2. If there are new workflows you need to configure, follow the configuration steps as outlined in the Configuration section below.

If you are updating an installation that was performed using the tar.gz distribution, it is recommended that you simply install the new version into a new directory.  Since everything (aside from the service files copied to /etc/init.d) is contained within a single directory, the new installation should not interfere with previous installations.  Note that if you do not make any changes to the service files copied to /etc/init.d, they will continue to use the older version.  Update the IPF_ETC_PATH, IPF_VAR_PATH, and PROGRAM (with full path to ipf_workflow program) to the values corresponding to your updated installation to utilize the updated version of ipf-xsede.

## Configuring IPF

If you are upgrading to IPF 1.4 from IPF 1.3, you MUST re-run the ipf_configure_xsede script to re-generate your workflow definition files.  If you do not, you will run into errors where IPF can't infer which step to use.

To make configuration easier, an `ipf_configure_xsede` script is provided in the bin directory (in /usr/bin if you installed RPMs, otherwise in $INSTALL_DIR/ipf-VERSION/ipf/bin).
This script will ask you questions and generate workflow definition files and example init files.  If you intend to publish module (or extended attribute module) information,
you are advised to set the environment variable MODULEPATH to point to the location of the module files before running ipf_configure_xsede.  If you intend to publish the service workflow,
you are advised to set SERVICEPATH to point to the location of the service definition files before running ipf_configure_xsede (more on this below).

* `ipf_configure_xsede` should be run as the user that will run the information gathering workflows

* `ipf_configure_xsede` will attempt to discover the XSEDE name of your resource using the xdresourceid program. If you have the xdresourceid program installed on your server, load it into your command line environment before running ipf_configure_xsede.

* The preferred way to authenticate is via an X.509 host certificate and key. You can place these files wherever you like (the configuration program will ask you for their location), but the default locations are /etc/grid-security/xdinfo-hostcert.pem and /etc/grid-security/xdinfo-hostkey.pem. These files must be readable by the user that runs the information gathering workflows.

* Submit an XSEDE ticket to authoritze your server to publish XSEDE's RabbitMQ services. If you will authenticate via X.509, include the output of 'openssl x509 -in path/to/cert.pem -nameopt RFC2253 -subject -noout' in your ticket. If you will authenticate via username and password, state that and someone will contact you.

Note: The xdinfo user as created by the ipf-xsede rpm installation has /bin/nologin set as its shell by default. This is because for most purposes, the xdinfo user doesn’t need an interactive shell. However, for some of the initial setup, it is easiest to use the xdinfo user with an interactive shell (so that certain environment variables like MODULEPATH can be discovered.)  Thus, it is recommended that the configuration steps are run after something like the following:

    $ sudo -u xdinfo -s /bin/bash --rcfile /etc/bashrc -i
    $ echo $MODULEPATH
    $ echo $SERVICEPATH

Execute:

    $ ipf_configure_xsede

Follow the instructions and enter the requested information. If you encounter any errors or the script does not
cover your situation, please submit an XSEDE ticket.

When the script exits, the etc/ipf/workflow/glue2/ directory will contain a set of files RESOURCE_NAME_*.json
that describe the information gathering workflows you have configured and etc/ipf/init.d will contain ipf-RESOURCE_NAME_*
files which are the init scripts you have configured.

As root, copy the etc/ipf/init.d/ipf-RESOURCE_NAME-* files into /etc/init.d. Your information gathering workflows
can then be enabled, started, and stopped in the usual ways.  You may need to perform a 'chkconfig --add' or
equivalent for each service.


## Configuring Compute workflow to filter by queue or partition

IPF 1.5 includes the ability to filter the Compute workflow by queue or partition, if you are using SLURM.  This is primarily intended for sites that need to consider GPU nodes as separate resources for the purposes of computing utilization, etc.  

To set parameters of Queues and/or Partitions for filtering, one must manually edit the workflow configuration files.

For example, on can set a params: partitions: inside the compute workflow in the ExectutionEnvironmentsStep as below:

{
           "name": "ipf.glue2.slurm.ExecutionEnvironmentsStep",
           "params": {
               "partitions": "+GPU -RM -LM -XLM -DBMI"
           }
       }

This will filter such that only the nodes in the GPU partition are considered for the Execution Environment.
A similar parameter, “queues” will filter by queue:
{
           "name": "ipf.glue2.slurm.ExecutionEnvironmentsStep",
           "params": {
               "queues": "+DBMI-GPU -DBMI -RM -RM-shared -RM-small -LM -XLM -GPU -GPU-shared"
           }
       }

These parameters can be mixed and matched, and can be applied at other steps as well (ComputingSharesStep, etc.) though I believe that when they are applied at the ExecutionEnvironmentsStep, that constrains the set of nodes considered for all other stats (as they are all computed as parts of ExecutionEnvironments).

## Configuring the Batch Scheduler Job Events Workflow

### Torque
It is necessary for Torque to log at the correct level in order for IPF to be able to parse the messages that it uses in
determining state.  Furthermore, the logging level of Torque can be confusing, as it has both a log_level and a log_events
(which is a bitmask).  The most important setting is that log_events should be set to 255.  This ensures that all types
of events are logged.  You can check the setting on your Torque installation by using "qmgr".

### SLURM
The SLURM logs must be in a directory that is local to and accessible to the IPF installation.
`ipf_configure_xsede` allows one to set this location for the workflow.


## Configuring Network Service Files
Each service.conf file needs to define the fields Name, Version, Endpoint, and Capability.

The Name field refers to the GLUE2 Primary protocol name supported by the service endpoint, as seen in the table below.

Each service can have multiple capabilities, but each line is a key/value pair, so to publish multiple capabilities for a service,
have a line that starts "Capability = " for each value.  (see example below).  The Capability fields describe what the service at
the endpoint URL supports.

Valid Capability values are listed in the table below.  Please edit your service.conf files to include appropriate Capability values.

A key/value pair for SupportStatus in your service.conf file will override the default, which is the support status of your service
as published in RDR.

_________________________________________________________________________
A table of valid Name, Version and Capability values:

    Name                Version        Capability
    org.globus.gridftp  {5,6}.y.z      data.transfer.striped
                                       data.transfer.nonstriped
        
    org.globus.gram     {5,6}.y.z      executionmanagement.jobdescription
                                       executionmanagement.jobexecution
                                       executionmanagement.jobmanager
    
    org.globus.openssh  5.y.z          login.remoteshell
                                       login.remoteshell.gsi
    eu.unicore.tsf      {6,7}.y.z      executionmanagement.jobdescription
                                       executionmanagement.jobexecution
                                       executionmanagement.jobmanager
    
    eu.unicore.bes      {6,7}.y.z      executionmanagement.jobdescription
                                       executionmanagement.jobexecution
                                       executionmanagement.jobmanager
    
    eu.unicore.reg      {6,7}.y.z      Information.publication    

Sample Service publishing file:

    #%Service1.0###################################################################
    ##
    ## serviceinfofiles/org.globus.gridftp-6.0.1.conf
    ##
    
    Name = org.globus.gridftp
    Version = 6.0.1
    Endpoint = gsiftp://$GRIDFTP_PUBLIC_HOSTNAME:2811/
    Extensions.go_transfer_xsede_endpoint_name = "default"
    Capability = data.transfer.striped
    Capability = data.transfer.nonstriped
    SupportStatus = testing


## Software Module Publishing Best Practices

The IPF Software Module workflow publishes information about locally installed software available through modules or Lmod.
IPF tries to make intelligent inferences from the system installed modules files when it publishes software information.
There are some easy ways, however, to add information to your module files that will enhance/override the information
otherwise published.

The Modules workflows traverses your MODULEPATH and infers fields such as Name and Version from the directory
structure/naming conventions of the module file layout. Depending on the exact workflow steps, fields such as Description
may be blank, or inferred from the stdout/stderr text of the module.  However, the following fields can always
be explicitly added to a module file:

    Description:
    URL:
    Category:
    Keywords:
    SupportStatus:
    SupportContact:

Each field is a key: value pair.  The IPF workflows are searching the whole text of each module file for these fields.
They may be placed in a module-whatis line, or in a comment, and IPF will still read them.

The URL field should point to local user documentation.

The Category field may contain one or more comma separated fields of science or software categories. XSEDE's
official fields of science are listed at `https://info.xsede.org/wh1/xdcdb/v1/fos/?hierarchy=true`. Some
recommended software categories are: data, compiler,  language, debugger, profiler, optimization, system, utilities.
Category values are discoverable in the Research Software Portal in the software *Topics* field.

The Keywords field may contain any other desired keywords.

The SupportStatus field should be: development, testing, or production.

The SupportContact field must contain either:
* the exact URL:
`https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/globalid/helpdesk.xsede.org/`

* another URL that returns a JSON document formatted exactly like the one shown above (but with different values)

* or a one-liner JSON blob of the form:
`[{"GlobalID":"helpdesk.xsede.org","Name":"XSEDE Help Desk","Description":"XSEDE 24/7 support help desk","ShortName":"XSEDE","ContactEmail":"help@xsede.org","ContactURL":"https://www.xsede.org/get-help","ContactPhone":"1-866-907-2383"}]`

IMPORTANT:
* The XSEDE user portal only displays software with a SupportContact containing the exact URL above.
* Modules that do not have a SupportContact can have a default value assigned by the Workflow


All XSEDE registered support contact organizations are found at: `https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/`.
To register a new support contact e-mail help@xsede.org using the Subject: Please register a new Support Contact Organization in the CSR.

`ipf_configure_xsede` offers the opportunity to define a default SupportContact that is published for every module that does not define its own.  By default, this value is: `https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/globalid/helpdesk.xsede.org/`

Example:

    #%Module1.0#####################################################################
    ##
    ## modulefiles/xdresourceid/1.0
    ##
    module-whatis "Description: XSEDE Resource Identifier Tool"
    module-whatis "URL: http://software.xsede.org/development/xdresourceid/"
    module-whatis "Category: System tools"
    module-whatis "Keywords: information"
    module-whatis "SupportStatus: testing"
    module-whatis "SupportContact: https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/globalid/helpdesk.xsede.org/"

However, IPF would read these just as well if they were:

    #%Module1.0#####################################################################
    ##
    ## modulefiles/xdresourceid/1.0
    ##
    #module-whatis "Description: XSEDE Resource Identifier Tool"
    # "URL: http://software.xsede.org/development/xdresourceid/"
    # Random text that is irrelevant "Category: System tools"
    # module-whatis "Keywords: information"
    module-whatis "SupportStatus: testing"
    module-whatis "SupportContact: https://info.xsede.org/wh1/xcsr-db/v1/supportcontacts/globalid/helpdesk.xsede.org/"

With this in mind, XSEDE recommends that you add these fields to relevant module files.
The decision on whether to include them as module-whatis lines (and therefore visible as
such to local users) or to include them as comments is left to the site admins.

## Testing

1) To test the extended attribute modules workflow, execute:

    # service ipf-RESOURCE_NAME-glue2-extmodules start

This init script starts a workflow that periodically gathers (every hour by default) and publishes module information containing extended attributes.

The log file is in /var/ipf/RESOURCE_NAME_modules.log (or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_extmodules.log) and should contain messages resembling:

    2013-05-30 15:27:05,309 - ipf.engine - INFO - starting workflow extmodules
    2013-05-30 15:27:05,475 - ipf.publish.AmqpStep - INFO - step-3 - publishing representation ApplicationsOgfJson of Applications lonestar4.tacc.teragrid.org
    2013-05-30 15:27:05,566 - ipf.publish.FileStep - INFO - step-4 - writing representation ApplicationsOgfJson of Applications lonestar4.tacc.teragrid.org
    2013-05-30 15:27:06,336 - ipf.engine - INFO - workflow succeeded

If any of the steps fail, that will be reported and an error message and stack trace should appear. Typical failures are caused by the environment not having specific variables or commands available.

This workflow describes your modules as a JSON document containing GLUE v2.0 Application Environment and Application Handle objects. This document is published to the XSEDE messaging services in step-3 and is written to a local file in step-4. You can examine this local file in /var/ipf/RESOURCE_NAME_apps.json. If you see any errors in gathering module information, please submit an XSEDE ticket to SD&I.


2) To test the compute workflow, execute:

    # service ipf-RESOURCE_NAME-glue2-compute start

This init script starts a workflow that periodically gathers (every minute by default) and publishes information about your compute resource. This workflow generates two types of documents. The first type describes the current state of your resource. This document doesn't contain sensitive information and XSEDE makes it available without authentication. The second type describes the queue state of your resource, contains sensitive information (user names), and will only be made available to authenticated XSEDE users.

The log file is in /var/ipf/RESOURCE_NAME_compute.log (or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_compute.log) and should contain messages resembling:

    2013-05-30 15:50:43,590 - ipf.engine - INFO - starting workflow sge_compute
    2013-05-30 15:50:45,403 - ipf.publish.AmqpStep - INFO - step-12 - publishing representation PrivateOgfJson of Private stampede.tacc.teragrid.org
    2013-05-30 15:50:45,626 - ipf.publish.FileStep - INFO - step-14 - writing representation PrivateOgfJson of Private stampede.tacc.teragrid.org
    2013-05-30 15:50:45,878 - ipf.publish.AmqpStep - INFO - step-11 - publishing representation PublicOgfJson of Public stampede.tacc.teragrid.org
    2013-05-30 15:50:46,110 - ipf.publish.FileStep - INFO - step-13 - writing representation PublicOgfJson of Public stampede.tacc.teragrid.org
    2013-05-30 15:50:46,516 - ipf.engine - INFO - workflow succeeded

Typical failures are caused by the execution environment not having specific commands available. Review the environment setup in the init script.

You can examine /var/ipf/RESOURCE_NAME_compute.json (or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_compute.json) to determine if the description of your resource is accurate. You can also exampine /var/ipf/RESOURCE_NAME_activities.json ( or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_activities.json) to determine if the description of the jobs being managed by your resource is correct.

3) To test the activity workflow, execute:

    # service ipf-RESOURCE_NAME-glue2-activity start

This init script starts a long-running workflow that watches your scheduler log files and publishes information about jobs as they are submitted and change state.

The log file is in /var/ipf/RESOURCE_NAME_activity.log (or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_activity.log) and should contain messages resembling:

    2013-05-30 16:04:26,030 - ipf.engine - INFO - starting workflow pbs_activity
    2013-05-30 16:04:26,038 - glue2.pbs.ComputingActivityUpdateStep - INFO - step-3 - running
    2013-05-30 16:04:26,038 - glue2.log - INFO - opening file 27-6930448 (/opt/pbs6.2/default/common/reporting)
    2013-05-30 16:05:50,067 - glue2.log - INFO - reopening file 27-6930448 (/opt/pbs6.2/default/common/reporting)
    2013-05-30 16:05:50,089 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226387.user.resource.xsede.org
    2013-05-30 16:05:50,493 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226814.user.resource.xsede.org
    2013-05-30 16:06:12,109 - glue2.log - INFO - reopening file 27-6930448 (/opt/pbs6.2/default/common/reporting)
    2013-05-30 16:06:12,361 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226867.user.resource.xsede.org
    2013-05-30 16:06:12,380 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226868.user.resource.xsede.org
    2013-05-30 16:06:12,407 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226788.user.resource.xsede.org
    2013-05-30 16:06:12,428 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226865.user.resource.xsede.org
    2013-05-30 16:06:12,448 - ipf.publish.AmqpStep - INFO - step-4 - publishing representation ComputingActivityOgfJson of ComputingActivity 1226862.user.resource.xsede.org
    ...

You can look at the activity information published in /var/ipf/RESOURCE_NAME_activity.json (or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_activity.json). This file contains the sequence of activity JSON documents published.

4) To test the Abstract Service (services) workflow, execute:

    # service ipf-RESOURCE_NAME-glue2-services start

This init script starts a workflow that periodically gathers (every hour by default) and publishes service information from the service definition files. 

The log file is in /var/ipf/RESOURCE_NAME_services.log (or $INSTALL_DIR/ipf/var/ipf/RESOURCE_NAME_services.log) and should contain messages resembling:

    2013-05-30 15:27:05,309 - ipf.engine - INFO - starting workflow s
    2013-05-30 15:27:05,475 - ipf.publish.AmqpStep - INFO - step-3 - publishing representation ASOgfJson of AbstractServices lonestar4.tacc.teragrid.org
    2013-05-30 15:27:05,566 - ipf.publish.FileStep - INFO - step-4 - writing representation ASOgfJson of AbstractServices lonestar4.tacc.teragrid.org
    2013-05-30 15:27:06,336 - ipf.engine - INFO - workflow succeeded

If any of the steps fail, that will be reported and an error message and stack trace should appear. Typical failures are caused by the environment not having specific variables or commands available.

This workflow describes your modules as a JSON document containing GLUE v2.0 Application Environment and Application Handle objects. This document is published to the XSEDE messaging services in step-3 and is written to a local file in step-4. You can examine this local file in /var/ipf/RESOURCE_NAME_apps.json. If you see any errors in gathering module information, please submit an XSEDE ticket to SD&I.

## Log File Management

The log files described above will grow over time. The logs are only needed for debugging, so they can be deleted whenever you wish. logrotate is a convenient tool for creating archival log files and limiting the amount of files kept. One note is that the ipf workflows keep the log files open while they run, so you should either use the copytruncate option or have a post-rotate statement to restart the corresponding ipf service.

# References

(1) IPF is open source and maintained at [https://github.com/XSEDE/ipf](https://github.com/XSEDE/ipf.).
(2) [XSEDE Information Services](https://info.xsede.org/).
(3) [XSEDE Software and Services Table for Service Providers](https://www.ideals.illinois.edu/handle/2142/85886).
(4) [Resource Description Repository "RDR"](https://rdr.xsede.org/).
(5) [GLUE2 Standard Format](https://www.ogf.org/documents/GFD.147.pdf).

# Appendix:  Configuration File Background

There are several files associated with IPF, both pre and post configuration that help determine how workflows are configured and how and when they run.

## Pre-configuration templates
Depending on how you installed IPF, the IPF source tree can be found in various locations.  
If you used RPM to install, the source code can be found at /usr/lib/python3.6/site-packages/ipf/.  Note, however, that the $IPF_ETC dir for an RPM install is /etc/ipf (that is to say, inside the canonical /etc directory)
If you used pip to install, the source code can be found in your python's site_packages/ipf/ directory.  To find the site_packages directory for your python, you can run: 
    $ python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])'
The pip-installed IPF_ETC path is this directory above, with /etc/ipf/ added to the end, e.g. /usr/lib/python3.6/site-packages/etc/ipf

If you used a tarball or git checkout, you should be able to find the source code on your filesystem yourself.

IPF ships with pre-configuration workflow templates for the various schedulers.
They can be found in the IPF_ETC directory in the $IPF_ETC/workflow/templates directory.
The template files as currently constructed are:
    generic_publish.json
    generic_print.json
    glue2/lmod.json
    glue2/serviceremotepublish.json
    glue2/moab_pbs_compute.json
    glue2/extmodules.json
    glue2/extmodulesremote.json
    glue2/condor_compute.json
    glue2/abstractservice.json
    glue2/pbs_activity.json
    glue2/sge_activity.json
    glue2/ipfinfo_publish.json
    glue2/sge_compute.json
    glue2/pbs_compute.json
    glue2/slurm_activity.json
    glue2/modules.json
    glue2/slurm_compute.json
    glue2/openstack_compute.json
    glue2/catalina_pbs_compute.json

These workflow templates are automatically used in workflow configuration via the ipf_configure_xsede script.

## Post-configuration workflow files
After you configure your workflows, the configured workflows will be represented by json files in $IPF_ETC/workflow and/or $IPF_ETC/workflow/glue2.
There will be a json file for each configured workflow, and various workflows will have a second "periodic" workflow that calls the other at a configurable delay.
These workflow files can be invoked by 
    $INSTALL_DIR/ipf-VERSION/ipf/bin/ipf_workflow <workflow.json>
However, in production, they are more commonly invoked by init scripts described below.

## Workflow init scripts
The ipf_configure_xsede script generates an init script for each workflow you configure, and puts them in $IPF_ETC/init.d/
Each script runs one workflow, on a periodic basis (using the periodic workflows described above).
It is important to note that the scripts in $IPF_ETC/init.d are NOT automatically configured to be run by the operating system: this must be done manually, typically by being copied into the system /etc/init.d directory as part of the installation and configuration process documented in this file.  Thus, to see what is actually being used to invoke the workflows in production, one must find the operating system location of init scripts, and see what is configured there.
