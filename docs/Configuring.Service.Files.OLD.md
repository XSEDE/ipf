# ipf-xsede %VER%-%REL
# Configuring Service Files

Service description files should be placed in a single directory, such /etc/ipf/services/,
$IPF/etc/services for a non RPM install, or some other directory. You must then set the
SERVICEPATH environment variable to point to the directory with the service description files.
This will get encoded by ipf_configure_xsede into the periodic workflows, so that the
services periodic workflow will be able to find the services files.

IPF will consider all filenames within SERVICEPATH to be valid service description files,
except filenames that start with ".".  In other words, both ExampleService.conf and
ExampleService.noreg would get published, but .ExampleService.conf will not.

Each service description file, such as myservice.conf, needs define a Name, Version,
Endpoint, and Capability variable.

The Name field should contain the GLUE2 Primary protocol name supported by the
service endpoint, as seen in the table below.

Each service can have multiple capabilities, but each line is a key/value pair, so to publish
multiple capabilities for a service, have a line that starts "Capability = " for each value. 
(see example below).

An optional SupportStatus variable in a service description file will override the
default, which is the support status of your service as published in RDR.

## Table of valid Name,version and capability values

<pre>
Name                            Version       Capability
org.globus.gridftp         {5,6}.y.z      data.transfer.striped
                                                        data.transfer.nonstriped

org.globus.gram		{5,6}.y.z     executionmanagement.jobdescription
                                                        executionmanagement.jobexecution
                                                        executionmanagement.jobmanager

org.globus.openssh 	5.y.z           login.remoteshell
                                                        login.remoteshell.gsi
eu.unicore.tsf 		       {6,7}.y.z      executionmanagement.jobdescription
                                                        executionmanagement.jobexecution
                                                        executionmanagement.jobmanager

eu.unicore.bes             {6,7}.y.z      executionmanagement.jobdescription
                                                        executionmanagement.jobexecution
                                                        executionmanagement.jobmanager

eu.unicore.reg 		{6,7}.y.z     Information.publication

org.xsede.gpfs 		3.              data.access.flatfiles

org.xsede.genesisII	2.y.z          data.access.flatfiles
                                                        data.naming.resolver
</pre>

## Sample Service publishing file

<pre>
#%Service1.0################################################################### ##
## serviceinfofiles/org.globus.gridftp-6.0.1.conf
##

Name = org.globus.gridftp
Version = 6.0.1
Endpoint = gsiftp://$GRIDFTP_PUBLIC_HOSTNAME:2811/
Extensions.go_transfer_xsede_endpoint_name = "default"
Capability = data.transfer.striped
Capability = data.transfer.nonstriped
SupportStatus = testing
</pre>
