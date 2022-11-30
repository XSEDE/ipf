# ipf-xsede %VER%-%REL
# Configuring Service Files

Our recommendations on how to configure Service files have changed somewhat from earlier versions of IPF.  Notably:

You no longer need to (and indeed should not) publish Globus Connect Server endpoints because ACCESS will automatically discover and publish these from Globus itself.

When publishing OpenSSH services, please reference the following example:

## Sample Service publishing file

<pre>
#%Service1.0################################################################### ##
## serviceinfofiles/org.openssh-8.x.conf
##

Name = org.openssh
Version = 8.x
Endpoint = <HOSTNAME>:<PORT>
#One or more of the following capability lines:
Capability = login.shell.local-password
Capability = login.shell.local-password-mfa 
Capability = login.shell.access-password-mfa
Capability = login.shell.gsi
Capability = login.shell.pubkey
Capability = login.shell.pubkey-mfa 

SupportStatus = <development|testing|production>
##end openssh example file
</pre>

The basics of how service files are used by IPF remains the same:

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
default, which is the support status of your service as published in CiDeR.
