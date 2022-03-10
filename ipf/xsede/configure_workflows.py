
###############################################################################
#   Copyright 2015 The University of Texas at Austin                          #
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
###############################################################################

import copy
import getpass
import json
import os
import socket
import subprocess
import threading
import urllib.request
import urllib.error
import urllib.parse
import time
import sysconfig
import argparse

#######################################################################################################################

def parseargs():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--resource_name', \
                        help='Set the resource name')
    parser.add_argument('--organization_name', \
                        help='Set the organization name')
    parser.add_argument('--city', \
                        help='Set the city')
    parser.add_argument('--country', \
                        help='Set the country')
    parser.add_argument('--latitude', \
                        help='Set the latitude')
    parser.add_argument('--longitude', \
                        help='Set the longitude')
    parser.add_argument('--rpm', action='store_true', \
                        help='IPF was installed from RPM')
    parser.add_argument('--pip', action='store_true', \
                        help='IPF was installed using pip')
    parser.add_argument('--base_dir', \
                        help='Set the base directory')
    parser.add_argument('--scheduler', \
                        help='set the scheduler name')
    parser.add_argument('-scheduler_params', action='store', \
                        help='comma delimited key:value pairs for parameters for your scheduler')
    parser.add_argument('--amqp_username', \
                        #action='store_const',const='username', dest='mode',\
                        help='Username for publishing to XSEDE AMQP. Not needed if using certificate')
    parser.add_argument('--amqp_certificate', \
                        #action='store_const',const='certificate', dest='mode',\
                        help='Location of certificate for publishing to XSEDE AMQP. Not needed if using username')
    parser.add_argument('--amqp_password', \
                        help='Password for publishing to XSEDE AMQP. Not needed if using certificate')
    parser.add_argument('--amqp_certificate_key', \
                        help='Location of certificate key for publishing to XSEDE AMQP. Not needed if using username')
    parser.add_argument('--modulepath', action='store_true', \
                        help='MODULEPATH for software publishing workflow')
    parser.add_argument('--servicepath', action='store_true', \
                        help='SERVICEPATH for service publishing workflow')
    parser.add_argument('--workflows', \
                        help='Comma delimited list of workflows to configure')
    parser.add_argument('--software', action='store_true', \
                        help='Configure the software publishing service')
    parser.add_argument('--services', action='store_true', \
                        help='Configure the services publishing service')
    parser.add_argument('--e', action='store_true', \
                        help='Configure the software publishing service')
    parser.add_argument('--workflowtemplate', \
                        help='Path to configured workflow to use as template for new workflow')
    parser.add_argument('--publish_to_xsede', action='store_true', \
                        help='Configure the services to publish to XSEDE')
    parser.add_argument('--compute_interval', \
                        help='Interval in seconds for the compute workflow to wait before rerunning')
    parser.add_argument('--modules', \
                        help='Any modules that need to be loaded in the init scripts for workflows')
    parser.add_argument('--environment', \
                        help='Any environment variables that needs to be loaded in the init scripts for workflows, such as \n * batch scheduler commands that need to be in PATH \n * scheduler-related environment variables may need to be set')
    parser.add_argument('--pbs_log_dir', \
                        help='The full path PBS log dir')
    parser.add_argument('--sge_reporting_log', \
                        help='The full path (including filename) for your SGE reporting log')
    parser.add_argument('--slurmctl_log', \
                        help='The full path (including filename) for your slurmctl.log file')
    parser.add_argument('--support_contact', \
                        help='The support contact URL to be published in your ExtModules workflow')
    parser.add_argument('--modules_interval', \
                        help='Interval in hours for the ExtModules workflow to wait before rerunning')
    parser.add_argument('--services_interval', \
                        help='Interval in hours for the AbstractServices workflow to wait before rerunning')

    return parser.parse_args()


def configure():
    args = parseargs()
    #print()
    #print("This script asks you for information and configures your IPF installation.")
    #print("  This script backs up your existing configuration, by renaming the existing configuration files with .backup-TIMESTAMP")

    template_json = getTemplateJson(args.workflowtemplate)

    if args.resource_name:
        resource_name = args.resource_name
    else:
        resource_name = getResourceName(template_json)

    setBaseDir(args)
   
    if args.workflows: 
        for workflow in args.workflows.split(","):
            print("** Configuring workflow: %s" % workflow)
            if workflow == "compute":
               configure_compute_workflow(resource_name,args,template_json)
            if workflow == "activity":
               configure_activity_workflow(resource_name,args,template_json)
            if workflow == "extmodules":
               configure_extmodules_workflow(resource_name,args,template_json)
            if workflow == "services":
               configure_services_workflow(resource_name,args,template_json)
            if workflow == "ipfinfo":
               configure_ipfinfo_workflow(resource_name,args,template_json)
    else:
        print('\nPlease specify one or more workflows with the "--workflows <workflowlist>" command line option.  \nNote that "<workflowlist>" should be a comma delimited list that includes one or more of:\n     compute\n     activity\n     extmodules\n     services\n     ipfinfo\n')
        raise SystemExit
    

    return


#######################################################################################################################

# need to test this with an xdresourceid program

def configure_compute_workflow(resource_name,args,template_json):
    if args.scheduler:
        sched_name = args.scheduler
    else:
        sched_name = getSchedulerName()
    #if template_json is a compute workflow, then compute_json should be template_json
    compute_json = getComputeJsonForScheduler(sched_name,template_json)
    setResourceName(resource_name, compute_json)
    setLocation(compute_json,args,template_json)
    updateFilePublishPaths(resource_name, compute_json)
    if (args.publish_to_xsede):
        addXsedeAmqpToWorkflow("compute",compute_json, template_json, args)
    writeComputeWorkflow(resource_name, compute_json)
    writePeriodicComputeWorkflow(resource_name,args)

    module_names = getModules(args)
    env_vars = getEnvironmentVariables(args)
    writeComputeInit(resource_name, module_names, env_vars)

def configure_activity_workflow(resource_name,args,template_json):
    if args.scheduler:
        sched_name = args.scheduler
    else:
        sched_name = getSchedulerName()

    activity_json = getActivityJsonForScheduler(sched_name,template_json)
    setResourceName(resource_name, activity_json)
    updateActivityLogFile(resource_name, activity_json, args)
    updateFilePublishPaths(resource_name, activity_json)
    if (args.publish_to_xsede):
        addXsedeAmqpToWorkflow("activity",activity_json, template_json, args)
    writeActivityWorkflow(resource_name, activity_json)

    module_names = getModules(args)
    env_vars = getEnvironmentVariables(args)
    writeActivityInit(resource_name, module_names, env_vars)


def configure_extmodules_workflow(resource_name,args,template_json):
    extmodules_json = getExtModulesJson(template_json)
    setSupportContact(extmodules_json,args)
    setResourceName(resource_name, extmodules_json)
    updateFilePublishPaths(resource_name, extmodules_json)
    if (args.publish_to_xsede):
        addXsedeAmqpToWorkflow("extmodules",extmodules_json, template_json, args)
    writeExtModulesWorkflow(resource_name, extmodules_json)
    writePeriodicExtModulesWorkflow(resource_name,args)

    module_names = getModules(args)
    env_vars = getEnvironmentVariables(args)
    writeExtModulesInit(resource_name, module_names, env_vars)

def configure_services_workflow(resource_name,args,template_json):
    services_json = getAbstractServicesJson(template_json)
    setResourceName(resource_name, services_json)
    updateFilePublishPaths(resource_name, services_json)
    if (args.publish_to_xsede):
        addXsedeAmqpToWorkflow("services",services_json, template_json, args)
    writeAbstractServicesWorkflow(resource_name, services_json)
    writePeriodicAbstractServicesWorkflow(resource_name,args)


    module_names = getModules(args)
    env_vars = getEnvironmentVariables(args)
    writeAbstractServicesInit(resource_name, module_names, env_vars)


def configure_ipfinfo_workflow(resource_name,args,template_json):
    ipfinfo_json = getIPFInfoJson(template_json)
    if (args.publish_to_xsede):
        addXsedeAmqpToWorkflow("ipfinfo",ipfinfo_json, template_json, args)
    writeIPFInfoWorkflow(ipfinfo_json)

    module_names = getModules(args)
    env_vars = getEnvironmentVariables(args)
    writeIPFInfoInit(resource_name, module_names, env_vars)

#######################################################################################################################
def getResourceName(template_json):
    if template_json is not None:
        for step_json in template_json["steps"]:
            if step_json["name"] == "ipf.sysinfo.ResourceNameStep":
                if "params" in step_json:
                    resource_name = step_json["params"]["resource_name"]
            return resource_name
    else:
        print('\nNo XSEDE resource name specified.  You must do one of:\n     * make sure xdresourceid is in your path\n     *use the command line option "--resource_name <name>"\n     *specify a template file that defines the resource name, using --workflowtemplate <file.json>')
        raise SystemExit
    return


def getTemplateJson(template_name):
    if template_name:
        if not testReadFile(template_name):
            raise Exception("No template file found at %s" % template_name)
        else:
            return readWorkflowFile(template_name)
    else:
        return None

def getComputeJsonForScheduler(sched_name,template_json):
    if template_json is not None:
        try:
            template_json["name"].index("_compute")
        except ValueError:
            pass
        else:
            return template_json
    return readWorkflowFile(os.path.join(getWorkflowTemplateGlueDir(), sched_name+"_compute.json"))


def getActivityJsonForScheduler(sched_name,template_json):
    if template_json is not None:
        try:
            template_json["name"].index("_activity")
        except ValueError:
            pass
        else:
            return template_json
    parts = sched_name.split("_")
    if len(parts) == 1:
        sched_name = sched_name
    elif len(parts) == 2:
        sched_name = parts[1]
    else:
        print("Warning: expected one or two parts in scheduler name - may not find _activity workflow file")
        sched_name = sched_name
    return readWorkflowFile(os.path.join(getWorkflowTemplateGlueDir(), sched_name+"_activity.json"))


def getExtModulesJson(template_json):
    if template_json is not None:
        try:
            template_json["name"].index("_extmodules")
        except ValueError:
            pass
        else:
            return template_json
    return readWorkflowFile(os.path.join(getWorkflowTemplateGlueDir(), "extmodules.json"))


def setSupportContact(extmodules_json,args):
    if args.support_contact:
        support_contact = args.support_contact
    else:
        support_contact = None
    for step_json in extmodules_json["steps"]:
        if step_json["name"] == "ipf.glue2.modules.ExtendedModApplicationsStep":
            if support_contact is not None:
                if step_json["params"]:
                    step_json["params"]["default_support_contact"] = support_contact
                else:
                    step_json["params"]={}
                    step_json["params"]["default_support_contact"] = getSupportContact()
            return
    raise Exception("didn't find an ExtendedModApplicationsStep to modify")


def getAbstractServicesJson(template_json):
    if template_json is not None:
        if _services in template_json["Name"]:
            return template_json
    return readWorkflowFile(os.path.join(getWorkflowTemplateGlueDir(), "abstractservice.json"))


def getIPFInfoJson(template_json):
    if template_json is not None:
        if _ipfinfo in template_json["Name"]:
            return template_json
    return readWorkflowFile(os.path.join(getWorkflowTemplateGlueDir(), "ipfinfo_publish.json"))


def getSchedulerName():
    names = []
    sched_dir = getWorkflowTemplateGlueDir()
    for file_name in os.listdir(sched_dir):
        if file_name.endswith("_compute.json"):
            parts = file_name.split("_")
            if len(parts) == 2:
                names.append(parts[0])
            else:
                names.append(parts[0]+"_"+parts[1])
    names = sorted(names)
    opts('\nPlease specify a scheduler using the "--scheduler <scheduler>" command line option.  You can choose from one of the following:', names)
    raise SystemExit


def setResourceName(resource_name, workflow_json):
    res_name = resource_name.split(".")[0]
    workflow_json["name"] = res_name + "_" + workflow_json["name"]
    for step_json in workflow_json["steps"]:
        if step_json["name"] == "ipf.sysinfo.ResourceNameStep":
            step_json["params"] = {}
            step_json["params"]["resource_name"] = resource_name
            return
    raise Exception("didn't find a ResourceNameStep to modify")


def setLocation(compute_json,args,template_json):
    if template_json is not None:
        for templatestep_json in template_json["steps"]:
            if templatestep_json["name"] == "ipf.glue2.location.LocationStep":
                if "params" in templatestep_json:
                    location = templatestep_json["params"]["location"]
                    for step_json in compute_json["steps"]:
                        if step_json["name"] == "ipf.glue2.location.LocationStep":    
                            step_json["params"]["location"]=copy.deepcopy(templatestep_json["params"]["location"])
    for step_json in compute_json["steps"]:
        if step_json["name"] == "ipf.glue2.location.LocationStep":
            updateLocationStep(step_json["params"]["location"],args)
            return
    raise Exception("didn't find a LocationStep to modify")


def updateLocationStep(params,args):
    #Command line options always override template
    if args.organization_name:
        params["Name"] = args.organization_name
    elif not params["Name"]:
        print('Please Specify an organization_name with "--organization_name"')
        raise SystemExit 
    if args.city:
        params["Place"] = args.city
    elif not params["Place"]:
        print('Please Specify a city with "--city"')
        raise SystemExit 
    if args.country:
        params["Country"] = args.country
    elif not params["Country"]:
        print('Please Specify a country with "--country"')
        raise SystemExit 
    if args.latitude:
        params["Latitude"] = args.latitude
    elif not params["Latitude"]:
        print('Please Specify a latitude with "--latitude"')
        raise SystemExit 
    if args.longitude:
        params["Longitude"] = args.longitude
    elif not params["Longitude"]:
        print('Please Specify a longitude with "--longitude"')
        raise SystemExit 



def updateFilePublishPaths(resource_name, workflow_json):
    res_name = resource_name.split(".")[0]
    for step_json in workflow_json["steps"]:
        if step_json["name"] == "ipf.publish.FileStep":
            step_json["params"]["path"] = res_name + \
                "_" + step_json["params"]["path"]

def addXsedeAmqpToWorkflow(workflow_name,workflow_json, template_json, args):
    if not args.publish_to_xsede:
        return False
    if workflow_name == "compute":
        publish_step = "ipf.glue2.compute.PublicOgfJson"
        exchange = "glue2.compute"
        description = "Publish compute resource description to XSEDE"
    elif workflow_name == "activity":
        publish_step = "ipf.glue2.computing_activity.ComputingActivityOgfJson"
        exchange = "glue2.computing_activity"
        description = "Publish job updates to XSEDE"
    elif workflow_name == "software":
        publish_step = "ipf.glue2.application.ApplicationsOgfJson"
        exchange = "glue2.applications"
        description = "Publish modules to XSEDE"
    elif workflow_name == "services":
        publish_step = "ipf.glue2.abstractservice.ASOgfJson"
        exchange = "glue2.compute"
        description = "Publish Services to XSEDE"
    elif workflow_name == "ipfinfo":
        publish_step = "ipf.ipfinfo.IPFInformationJson"
        exchange = "glue2.compute"
        description = "Publish IPFInfo to XSEDE"
    if args.amqp_certificate:
        cert_path = args.amqp_certificate
        if not testReadFile(cert_path):
            raise Exception("No certificate found at %s" % cert_path)
        
        if args.amqp_certificate_key:
            key_path = args.amqp_certificate_key
            if not testReadFile(key_path):
                raise Exception("No key found at %s" % key_path)
        username = None
        password = None
    elif args.amqp_username:
        username = args.amqp_username
        password = args.amqp_password
        cert_path = None
        key_path = None
    elif template_json is not None:
        try:
            template_json["name"].index("_"+workflow_name)
        except ValueError:
            #Template is not for workflow--copy section in
            for step in template_json["steps"]:
                #compute workflow has two publish steps, copy both
                if step["name"] == "ipf.publish.AmqpStep" and "xsede.org" in step["params"]["services"][0]:
                    if workflow_name == "compute" and step["description"] == "Publish description of current jobs to XSEDE":
                        publish_description = step["description"]
                    else:
                        publish_description = description
                    amqp_step = copy.deepcopy(step)
                    amqp_step["description"] = publish_description
                    amqp_step["params"]["publish"] = [publish_step]
                    amqp_step["params"]["exchange"] = exchange
                    workflow_json["steps"].append(amqp_step)
            return True
        else:
            #Template is for workflow--already has the section, just return
            return True
    else: 
        raise Exception("Certificate/key or username/password must be specified")
    #No template json to copy
    amqp_step = {}
    amqp_step["name"] = "ipf.publish.AmqpStep"
    amqp_step["description"] = description 
    amqp_step["params"] = {}
    amqp_step["params"]["publish"] = [publish_step]
    amqp_step["params"]["services"] = [
        "infopub.xsede.org", "infopub-alt.xsede.org"]
    amqp_step["params"]["vhost"] = "xsede"
    amqp_step["params"]["exchange"] = exchange
    amqp_step["params"]["ssl_options"] = {}
    amqp_step["params"]["ssl_options"]["ca_certs"] = "xsede/ca_certs.pem"
    if cert_path is not None:
        amqp_step["params"]["ssl_options"]["certfile"] = cert_path
        amqp_step["params"]["ssl_options"]["keyfile"] = key_path
    else:
        amqp_step["params"]["username"] = username
        amqp_step["params"]["password"] = password
    workflow_json["steps"].append(amqp_step)
    
    if workflow_name == "compute":
        amqp_step = copy.deepcopy(amqp_step)
        amqp_step["description"] = "Publish description of current jobs to XSEDE"
        amqp_step["params"]["publish"] = ["ipf.glue2.compute.PrivateOgfJson"]
        amqp_step["params"]["exchange"] = "glue2.computing_activities"
        workflow_json["steps"].append(amqp_step)
    return True


def updateActivityLogFile(resource_name, activity_json, args):
    res_name = resource_name.split(".")[0]
    for step in activity_json["steps"]:
        if not "ActivityUpdateStep" in step["name"]:
            continue
        step["params"]["position_file"] = res_name+"_activity.pos"
        if "pbs" in step["name"]:
            if "PBS_HOME" not in os.environ:
                print(
                    "  Warning: PBS_HOME environment variable not set - can't check for server_logs directory")
                default = None
            else:
                default = os.path.join(
                    os.environ["PBS_HOME"], "spool", "server_logs")
                testReadDirectory(log_dir)
            log_dir = args.pbs_log_dir or default
            if not testReadDirectory(log_dir):
                raise Exception("Logfile %s not found. Please specify full path for your PBS log dir with the --pbs_log_dir option" % log_file)
            step["params"]["server_logs_dir"] = log_dir
        elif "sge" in step["name"]:
            if "SGE_ROOT" not in os.environ:
                print(
                    "  Warning: SGE_ROOT environment variable not set - can't check for reporting file")
                default = None
            else:
                default = os.path.join(
                    os.environ["SGE_ROOT"], "default", "common", "reporting")
                testReadFile(log_file)
            log_dir = args.sge_reporting_log or default
            if not testReadFile(log_file):
                #return updateActivityLogFile(resource_name, activity_json)
                raise Exception("Logfile %s not found. Please specify full path for your SGE log dir with the --sge_reporting_log option" % log_file)
            step["params"]["reporting_file"] = log_file
        elif "slurm" in step["name"]:
            if os.path.exists("/usr/local/slurm/var/slurmctl.log"):
                default = "/usr/local/slurm/var/slurmctl.log"
            else:
                default = None
            log_file = args.slurmctl_log or default
            print("logfile is %s" % log_file)
            if log_file is not None and not testReadFile(log_file):
                #return updateActivityLogFile(resource_name, activity_json)
                raise Exception("Logfile %s not found. Please specify full path (including filename) for your slurmctl.log file with the --slurmctl option" % log_file)
            step["params"]["slurmctl_log_file"] = log_file
        else:
            raise Exception("ActivityUpdateStep isn't pbs, sge, or slurm")
        break


#######################################################################################################################


def getModules(args):
    if not args.modules:
        return None
    else:
        csv = args.modules
    return csv.split(",")


def getEnvironmentVariables(args):
    vars = {}
    if args.modulepath:
        _modulepath = args.modulepath
    else:
        _modulepath = None 
    if _modulepath is not None:
        vars["MODULEPATH"] = _modulepath
    if args.servicepath:
        _servicepath = args.servicepath
    else:
        _servicepath = None 
    if _servicepath is not None:
        vars["SERVICEPATH"] = _servicepath
    if args.environment:
        _envvars = args.environment.split(",")
        for _envvar in _envvars:
            (name,value) = _envvar.split("=")
            vars[name] = value
    return vars

#######################################################################################################################


def writeComputeWorkflow(resource_name, compute_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(), res_name+"_compute.json")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    print("  -> writing compute workflow to %s" % path)
    f = open(path, "w")
    f.write(json.dumps(compute_json, indent=4, sort_keys=True))
    f.close()


def writePeriodicComputeWorkflow(resource_name,args):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_compute_periodic"
    periodic_json["description"] = "Gather GLUE2 compute information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_compute.json"
    if args.compute_interval:
        interval_str = args.compute_interval
    else:
        interval_str = 60
    step_json["params"]["maximum_interval"] = int(interval_str)

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(), res_name +
                        "_compute_periodic.json")
    print("  -> writing periodic compute workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(periodic_json, indent=4, sort_keys=True))
    f.close()


def writeActivityWorkflow(resource_name, activity_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(), res_name+"_activity.json")
    print("  -> writing activity workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(activity_json, indent=4, sort_keys=True))
    f.close()


def writeModulesWorkflow(resource_name, modules_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(), res_name+"_modules.json")
    print("  -> writing modules workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(modules_json, indent=4, sort_keys=True))
    f.close()


def writeExtModulesWorkflow(resource_name, extmodules_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(), res_name+"_extmodules.json")
    print("  -> writing extended modules workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(extmodules_json, indent=4, sort_keys=True))
    f.close()


def writeAbstractServicesWorkflow(resource_name, services_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(), res_name+"_services.json")
    print("  -> writing abstract services workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(services_json, indent=4, sort_keys=True))
    f.close()


def writeIPFInfoWorkflow(ipfinfo_json):
    path = os.path.join(getWorkflowDir(), "ipfinfo_publish.json")
    print("  -> writing ipfinfo publish workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(ipfinfo_json, indent=4, sort_keys=True))
    f.close()


def writePeriodicExtModulesWorkflow(resource_name,args):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_extmodules_periodic"
    periodic_json["description"] = "Gather GLUE2 Extended module (Software) information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_extmodules.json"
    if args.modules_interval:
        interval_str = args.modules_interval
    else:
        interval_str = 1
    step_json["params"]["maximum_interval"] = int(interval_str) * 60 * 60

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(), res_name +
                        "_extmodules_periodic.json")
    print("  -> writing periodic extended modules (software) workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(periodic_json, indent=4, sort_keys=True))
    f.close()


def writePeriodicAbstractServicesWorkflow(resource_name,args):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_services_periodic"
    periodic_json["description"] = "Gather GLUE2 AbstractService information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_services.json"
    if args.services_interval:
        interval_str = args.services_interval
    else:
        interval_str = 1
    step_json["params"]["maximum_interval"] = int(interval_str) * 60 * 60

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(), res_name +
                        "_services_periodic.json")
    print("  -> writing periodic Abstract Services workflow to %s" % path)
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    f = open(path, "w")
    f.write(json.dumps(periodic_json, indent=4, sort_keys=True))
    f.close()


#######################################################################################################################

def writeComputeInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(), "etc", "ipf", "init.d",
                        "ipf-"+res_name+"-glue2-compute")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    name = "%s_compute_periodic\n" % res_name
    writeInit(resource_name, module_names, env_vars, name, path)


def writeActivityInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(), "etc", "ipf", "init.d",
                        "ipf-"+res_name+"-glue2-activity")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    name = "%s_activity\n" % res_name
    writeInit(resource_name, module_names, env_vars, name, path)


def writeModulesInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(), "etc", "ipf", "init.d",
                        "ipf-"+res_name+"-glue2-modules")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    name = "%s_modules_periodic\n" % res_name
    writeInit(resource_name, module_names, env_vars, name, path)


def writeExtModulesInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(), "etc", "ipf", "init.d",
                        "ipf-"+res_name+"-glue2-extmodules")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    name = "%s_extmodules_periodic\n" % res_name
    writeInit(resource_name, module_names, env_vars, name, path)


def writeAbstractServicesInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(), "etc", "ipf", "init.d",
                        "ipf-"+res_name+"-glue2-services")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    name = "%s_services_periodic\n" % res_name
    writeInit(resource_name, module_names, env_vars, name, path)


def writeIPFInfoInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(), "etc", "ipf", "init.d", "ipfinfo")
    if os.path.isfile(path):
        os.rename(path, path+".backup-" +
                  time.strftime('%Y-%M-%d-%X', time.localtime()))
    name = "ipfinfo_publish_periodic\n"
    writeInit(resource_name, module_names, env_vars, name, path)


def writeInit(resource_name, module_names, env_vars, name, path):
    res_name = resource_name.split(".")[0]

    in_file = open(os.path.join(getBaseDir(), "etc",
                                "ipf", "init.d", "ipf-WORKFLOW"), "r")
    out_file = open(path, "w")
    for line in in_file:
        if line.startswith("NAME="):
            out_file.write("NAME=%s\n" % name)
        elif line.startswith("WORKFLOW="):
            if name == "ipf_publish_periodic\n":
                out_file.write("WORKFLOW=${NAME}.json\n")
            else:
                out_file.write(line)
        elif line.startswith("IPF_USER="):
            out_file.write("IPF_USER=%s\n" % getpass.getuser())
        elif line.startswith("export IPF_ETC_PATH="):
            out_file.write("export IPF_ETC_PATH=%s\n" %
                           os.path.join(getBaseDir(), "etc/ipf"))
        elif line.startswith("export IPF_VAR_PATH="):
            out_file.write("export IPF_VAR_PATH=%s\n" %
                           os.path.join(getBaseDir(), "var/ipf"))
        elif "modules" in line and module_names != None:
            out_file.write(line)
            out_file.write("source %s\n" % os.path.join(
                os.environ["MODULESHOME"], "init", "bash"))
            for module_name in module_names:
                out_file.write("module load %s\n" % module_name)
        elif "environment variables" in line and len(env_vars) > 0:
            out_file.write(line)
            for name in env_vars:
                out_file.write("export %s=%s\n" % (name, env_vars[name]))
        else:
            out_file.write(line)
    in_file.close()
    out_file.close()

#######################################################################################################################


def getSupportContact():
    support_contact = "https://software.xsede.org/xcsr-db/v1/support-contacts/1553"
    return support_contact


def getGlueWorkflowDir():
    return os.path.join(getWorkflowDir(), "glue2")

def getWorkflowTemplateDir():
    return os.path.join(getWorkflowDir(), "templates")

def getWorkflowTemplateGlueDir():
    return os.path.join(getWorkflowTemplateDir(), "glue2")

def getWorkflowDir():
    return os.path.join(getBaseDir(), "etc", "ipf", "workflow")


_base_dir = None


def getBaseDir():
    global _base_dir
    if _base_dir is not None:
        return _base_dir
    return _base_dir

def setBaseDir(args):
    global _base_dir
    if args.base_dir:
       _base_dir = args.base_dir 
       return _base_dir
    if args.rpm:
       _base_dir = "/"
    elif args.pip:
        _base_dir = sysconfig.get_paths()["purelib"]
    else:
        print('\nNo base directory specified.  Please do one of the following:\n     *if you installed IPF from an RPM, specify the "--rpm" command line option.\n     *if you installed using pip, specify the "--pip" command line option.\n     *otherwise, use the "--base_dir <path>" command line option where <path> is the root of where you installed IPF.\n')
        raise SystemExit

    return _base_dir


def readWorkflowFile(path):
    f = open(path)
    text = f.read()
    f.close()
    return json.loads(text)

#######################################################################################################################


def question(text, default=None):
    print()
    if default is None:
        answer = input("%s: " % text)
        if answer == "":
            raise Exception("no input provided")
    else:
        answer = input("%s (%s): " % (text, default))
        if answer == "":
            return default
    return answer

def opts(text, opts, default=None):
    print()
    if default is None:
        print("%s:" % text)
    else:
        print("%s (%s):" % (text, default))
    for i in range(len(opts)):
        print("  (%d) %s" % ((i+1), opts[i]))

def options(text, opts, default=None):
    print()
    if default is None:
        print("%s:" % text)
    else:
        print("%s (%s):" % (text, default))
    for i in range(len(opts)):
        print("  (%d) %s" % ((i+1), opts[i]))
    answer = input(": ")
    if answer == "":
        if default is None:
            print("no options selected - pick a number")
            return options(text, opts, default)
        else:
            return default
    try:
        index = int(answer)
    except ValueError:
        print("enter a number")
        return options(text, opts, default)
    if index < 1 or index > len(opts):
        print("select an option between 1 and %d" % len(opts))
        return options(text, opts, default)
    return opts[index-1]

#######################################################################################################################


def testReadFile(path, print_warnings=True):
    if not os.path.exists(path):
        if print_warnings:
            print("  Warning: file %s doesn't exist" % path)
        return False
    if not os.access(path, os.R_OK):
        if print_warnings:
            print("  Warning: file %s can't be read by current user" % path)
        return False
    return True


def testReadDirectory(path, print_warnings=True):
    if not os.path.exists(path):
        if print_warnings:
            print("  Warning: directory %s doesn't exist" % path)
        return False
    if not os.path.isdir(path):
        if print_warnings:
            print("  Warning: %s is not a directory" % path)
        return False
    if not os.access(path, os.R_OK):
        if print_warnings:
            print("  Warning: directory %s can't be read by current user" % path)
        return False
    return True

#######################################################################################################################


if __name__ == "__main__":
    configure()
