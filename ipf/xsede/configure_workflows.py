
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
import urllib2

#######################################################################################################################

def configure():
    print
    print("This script asks you for information and configures your IPF installation.")
    print("  Warning: At the current time, this script overwrites your existing configuration, it does not modify it")

    resource_name = getResourceName()
    sched_name = getSchedulerName()
    compute_json = getComputeJsonForScheduler(sched_name)
    setResourceName(resource_name,compute_json)
    setLocation(compute_json)
    updateFilePublishPaths(resource_name,compute_json)
    addXsedeAmqpToCompute(compute_json)
    writeComputeWorkflow(resource_name,compute_json)
    writePeriodicComputeWorkflow(resource_name)

    print
    print("You may need to modify the default environment in your init scripts so that the information gathering works correctly. For example:")
    print("  * batch scheduler commands need to be in PATH")
    print("  * scheduler-related environment variables may need to be set")
    module_names = getModules()
    env_vars = getEnvironmentVariables()
    writeComputeInit(resource_name,module_names,env_vars)

    answer = options("Do you want to publish job updates? Your scheduler log files must be readable.",
                     ["yes","no"],"yes")
    if answer == "yes":
        activity_json = getActivityJsonForScheduler(sched_name)
        setResourceName(resource_name,activity_json)
        updateActivityLogFile(resource_name,activity_json)
        updateFilePublishPaths(resource_name,activity_json)
        addXsedeAmqpToActivity(activity_json,compute_json)
        writeActivityWorkflow(resource_name,activity_json)
        writeActivityInit(resource_name,module_names,env_vars)

    modules_type = getModulesType()
    if modules_type == "modules":
        modules_json = getModulesJson()
    elif modules_type == "lmod":
        modules_json = getLModJson()
    extmodules_json = getExtModulesJson()
    services_json = getAbstractServicesJson()
    setResourceName(resource_name,modules_json)
    setResourceName(resource_name,extmodules_json)
    setResourceName(resource_name,services_json)
    updateFilePublishPaths(resource_name,modules_json)
    updateFilePublishPaths(resource_name,extmodules_json)
    updateFilePublishPaths(resource_name,services_json)
    addXsedeAmqpToModules(modules_json,compute_json)
    addXsedeAmqpToExtModules(extmodules_json,compute_json)
    addXsedeAmqpToAbstractServices(services_json,compute_json)
    writeModulesWorkflow(resource_name,modules_json)
    writeExtModulesWorkflow(resource_name,extmodules_json)
    writeAbstractServicesWorkflow(resource_name,services_json)
    writePeriodicModulesWorkflow(resource_name)
    writePeriodicExtModulesWorkflow(resource_name)
    writePeriodicAbstractServicesWorkflow(resource_name)
    writeModulesInit(resource_name,module_names,env_vars)
    writeExtModulesInit(resource_name,module_names,env_vars)
    writeAbstractServicesInit(resource_name,module_names,env_vars)

#######################################################################################################################

# need to test this with an xdresourceid program
def getResourceName():
    try:
        process = subprocess.Popen(["xdresourceid"], stdout=subprocess.PIPE)
        out, err = process.communicate()
    except Exception, e:
        print("Failed to use xdresourceid to get resource name: %s" % e)
        xdresid_name = None
    else:
        xdresid_name = out.rstrip()
    resource_name = question("Enter the XSEDE resource name",xdresid_name)
    return resource_name

def getComputeJsonForScheduler(sched_name):
    return readWorkflowFile(os.path.join(getGlueWorkflowDir(),sched_name+"_compute.json"))

def getActivityJsonForScheduler(sched_name):
    parts = sched_name.split("_")
    if len(parts) == 1:
        sched_name = sched_name
    elif len(parts) == 2:
        sched_name = parts[1]
    else:
        print("Warning: expected one or two parts in scheduler name - may not find _activity workflow file")
        sched_name = sched_name
    return readWorkflowFile(os.path.join(getGlueWorkflowDir(),sched_name+"_activity.json"))

def getModulesJson():
    return readWorkflowFile(os.path.join(getGlueWorkflowDir(),"modules.json"))

def getExtModulesJson():
    return readWorkflowFile(os.path.join(getGlueWorkflowDir(),"extmodules.json"))

def getAbstractServicesJson():
    return readWorkflowFile(os.path.join(getGlueWorkflowDir(),"abstractservice.json"))

def getLModJson():
    return readWorkflowFile(os.path.join(getGlueWorkflowDir(),"lmod.json"))

def getSchedulerName():
    names = []
    for file_name in os.listdir(getGlueWorkflowDir()):
        if file_name.endswith("_compute.json"):
            parts = file_name.split("_")
            if len(parts) == 2:
                names.append(parts[0])
            else:
                names.append(parts[0]+"_"+parts[1])
    names = sorted(names)
    sched_name = options("Which scheduler/resource manager does this resource use?",names)
    return sched_name

def setResourceName(resource_name, workflow_json):
    res_name = resource_name.split(".")[0]
    workflow_json["name"] = res_name + "_" + workflow_json["name"]
    for step_json in workflow_json["steps"]:
        if step_json["name"] == "ipf.sysinfo.ResourceNameStep":
            step_json["params"] = {}
            step_json["params"]["resource_name"] = resource_name
            return
    raise Exception("didn't find a ResourceNameStep to modify")

def setLocation(compute_json):
    for step_json in compute_json["steps"]:
        if step_json["name"] == "ipf.glue2.location.LocationStep":
            updateLocationStep(step_json)
            return
    raise Exception("didn't find a LocationStep to modify")

def updateLocationStep(params):
    params["Name"] = question("Enter your organization",params.get("Name",None))
#    if params.get("Place",None) == None:
#        updateFromFreeGeoIp(params)
    params["Place"] = question("Enter your city",params.get("Place",None))
    params["Country"] = question("Enter your country",params.get("Country",None))
    params["Latitude"] = question("Enter your latitude",params.get("Latitude",None))
    params["Longitude"] = question("Enter your longitude",params.get("Longitude",None))

def updateFromFreeGeoIp(params):
    text = getFreeGeoIp()
    if text is None:
        text = getFreeGeoIp(True)
    if text is None:
        return None
    json_doc = json.loads(text)

    params["Place"] = json_doc["city"]
    params["Country"] = json_doc["country_code"]
    params["Latitude"] = float(json_doc["latitude"])
    params["Longitude"] = float(json_doc["longitude"])

def getFreeGeoIp(print_message=False):
    print("Querying for physical location...")
    thread = FreeGeoIp()
    thread.start()
    thread.join(60)
    if thread.isAlive():
        if print_message:
            print("Warning: Query to http:/freegeoip.net didn't complete")
            print("         Enter location information manually or re-run this configuration program")
        return None
    return thread.output

class FreeGeoIp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.output = None

    def run(self):
        host_name = socket.getfqdn()
        self.output = urllib2.urlopen("http://freegeoip.net/json/"+host_name).read()

def updateFilePublishPaths(resource_name, workflow_json):
    res_name = resource_name.split(".")[0]
    for step_json in workflow_json["steps"]:
        if step_json["name"] == "ipf.publish.FileStep":
            step_json["params"]["path"] = res_name + "_" + step_json["params"]["path"]

def addXsedeAmqpToCompute(compute_json, ask=True):
    answer = options("Do you wish to publish to the XSEDE AMQP service?",["yes","no"],"yes")
    if answer == "no":
        return
    answer = options("Will you authenticate using an X.509 certificate and key or a username and password?",
                     ["X.509","username/password"],"X.509")
    if answer == "X.509":
        cert_path = question("Where is your certificate?","/etc/grid-security/xdinfo-hostcert.pem")
        while not testReadFile(cert_path):
            cert_path = question("Where is your certificate?","/etc/grid-security/xdinfo-hostcert.pem")
        key_path = question("Where is your key?","/etc/grid-security/xdinfo-hostkey.pem")
        while not testReadFile(key_path):
            key_path = question("Where is your key?","/etc/grid-security/xdinfo-hostkey.pem")
        username = None
        password = None
    else:
        cert_path = None
        key_path = None
        username = question("What is your username?")
        password = question("What is your password?")

    amqp_step = {}
    amqp_step["name"] = "ipf.publish.AmqpStep"
    amqp_step["description"] = "Publish compute resource description to XSEDE"
    amqp_step["params"] = {}
    amqp_step["params"]["publish"] = ["ipf.glue2.compute.PublicOgfJson"]
    amqp_step["params"]["services"] = ["info1.dyn.xsede.org","info2.dyn.xsede.org"]
    amqp_step["params"]["vhost"] = "xsede"
    amqp_step["params"]["exchange"] = "glue2.compute"
    amqp_step["params"]["ssl_options"] = {}
    amqp_step["params"]["ssl_options"]["ca_certs"] = "xsede/ca_certs.pem"
    if cert_path is not None:
        amqp_step["params"]["ssl_options"]["certfile"] = cert_path
        amqp_step["params"]["ssl_options"]["keyfile"] = key_path
    else:
        amqp_step["params"]["username"] = username
        amqp_step["params"]["password"] = password
    compute_json["steps"].append(amqp_step)

    amqp_step = copy.deepcopy(amqp_step)
    amqp_step["description"] = "Publish description of current jobs to XSEDE"
    amqp_step["params"]["publish"] = ["ipf.glue2.compute.PrivateOgfJson"]
    amqp_step["params"]["exchange"] = "glue2.computing_activities"
    compute_json["steps"].append(amqp_step)

def updateActivityLogFile(resource_name, activity_json):
    res_name = resource_name.split(".")[0]
    for step in activity_json["steps"]:
        if not "ActivityUpdateStep" in step["name"]:
            continue
        step["params"]["position_file"] = res_name+"_activity.pos"
        if "pbs" in step["name"]:
            if "PBS_HOME" not in os.environ:
                print("  Warning: PBS_HOME environment variable not set - can't check for server_logs directory")
                log_dir = None
            else:
                log_dir = os.path.join(os.environ["PBS_HOME"],"spool","server_logs")
                testReadDirectory(log_dir)
            log_dir = question("Where is your server_logs directory?",log_dir)
            if not testReadDirectory(log_dir):
                return updateActivityLogFile(resource_name,activity_json)
            step["params"]["server_logs_dir"] = log_dir
        elif "sge" in step["name"]:
            if "SGE_ROOT" not in os.environ:
                print("  Warning: SGE_ROOT environment variable not set - can't check for reporting file")
                log_file = None
            else:
                log_file = os.path.join(os.environ["SGE_ROOT"],"default","common","reporting")
                testReadFile(log_file)
            log_file = question("Where is your reporting file?",log_file)
            if not testReadFile(log_file):
                return updateActivityLogFile(resource_name,activity_json)
            step["params"]["reporting_file"] = log_file
        elif "slurm" in step["name"]:
            if os.path.exists("/usr/local/slurm/var/slurmctl.log"):
                default = "/usr/local/slurm/var/slurmctl.log"
            else:
                default = None
            log_file = question("Where is your slurmctl.log file?",default)
            if not testReadFile(log_file):
                return updateActivityLogFile(resource_name,activity_json)
            step["params"]["slurmctl_log_file"] = log_file
        else:
            raise Exception("ActivityUpdateStep isn't pbs, sge, or slurm")
        break

def addXsedeAmqpToActivity(activity_json, compute_json):
    for step in compute_json["steps"]:
        if step["name"] == "ipf.publish.AmqpStep" and "xsede.org" in step["params"]["services"][0]:
                amqp_step = copy.deepcopy(step)
                amqp_step["description"] = "Publish job updates to XSEDE"
                amqp_step["params"]["publish"] = ["ipf.glue2.computing_activity.ComputingActivityOgfJson"]
                amqp_step["params"]["exchange"] = "glue2.computing_activity"
                activity_json["steps"].append(amqp_step)
                return
    raise Exception("didn't find AmqpStep in compute workflow")

def addXsedeAmqpToModules(modules_json, compute_json):
    for step in compute_json["steps"]:
        if step["name"] == "ipf.publish.AmqpStep" and "xsede.org" in step["params"]["services"][0]:
            amqp_step = copy.deepcopy(step)
            amqp_step["description"] = "Publish modules to XSEDE"
            amqp_step["params"]["publish"] = ["ipf.glue2.application.ApplicationsOgfJson"]
            amqp_step["params"]["exchange"] = "glue2.applications"
            modules_json["steps"].append(amqp_step)
            return
    raise Exception("didn't find AmqpStep in compute workflow")

def addXsedeAmqpToExtModules(modules_json, compute_json):
    for step in compute_json["steps"]:
        if step["name"] == "ipf.publish.AmqpStep" and "xsede.org" in step["params"]["services"][0]:
            amqp_step = copy.deepcopy(step)
            amqp_step["description"] = "Publish modules to XSEDE"
            amqp_step["params"]["publish"] = ["ipf.glue2.application.ApplicationsOgfJson"]
            amqp_step["params"]["exchange"] = "glue2.applications"
            modules_json["steps"].append(amqp_step)
            return
    raise Exception("didn't find AmqpStep in compute workflow")

def addXsedeAmqpToAbstractServices(modules_json, compute_json):
    for step in compute_json["steps"]:
        if step["name"] == "ipf.publish.AmqpStep" and "xsede.org" in step["params"]["services"][0]:
            amqp_step = copy.deepcopy(step)
            amqp_step["description"] = "Publish modules to XSEDE"
            amqp_step["params"]["publish"] = ["ipf.glue2.abstractservice.ASOgfJson"]
            amqp_step["params"]["exchange"] = "glue2.compute"
            modules_json["steps"].append(amqp_step)
            return
    raise Exception("didn't find AmqpStep in compute workflow")

#######################################################################################################################

def getModules():
    answer = options("Do you want to load any modules?",["yes","no"],"no")
    if answer == "no":
        return None
    csv = question("Enter a comma-separated list of modules to load")
    return csv.split(",")

def getEnvironmentVariables():
    vars = {}
    if "MODULEPATH" in os.environ:
         _modulepath = os.environ["MODULEPATH"]
	 print("MODULEPATH=%s" % _modulepath)
	 answer = options("is set in your environment.  Do you want to use this value in the Modules workflow?",["yes","no"],"yes")
         if answer == "no":
	    answer = options("do you want to set a different value for MODULEPATH for use in the Modules workflow?",["yes","no"],"yes")
	    if answer == "yes":
	       _modulepath = question("Enter the value for MODULEPATH")
	    else:
	       _modulepath = None
         if _modulepath is not None:
	    vars["MODULEPATH"] = _modulepath
    if "SERVICEPATH" in os.environ:
         _servicepath = os.environ["SERVICEPATH"]
	 print("SERVICEPATH=%s" % _servicepath)
	 answer = options("is set in your environment.  Do you want to use this value in the Services workflow?",["yes","no"],"yes")
         if answer == "no":
	    answer = options("do you want to set a different value for SERVICEPATH for use in the Services workflow?",["yes","no"],"yes")
	    if answer == "yes":
	       _servicepath = question("Enter the value for SERVICEPATH")
	    else:
	       _servicepath = None
         if _servicepath is not None:
	    vars["SERVICEPATH"] = _servicepath
    while True:
        if len(vars) > 0:
            print("current variables:")
            for key in sorted(vars.keys()):
                print("  %s = %s" % (key,vars[key]))
        answer = options("Do you want to set an environment variable?",["yes","no"],"no")
        if answer == "no":
            return vars
        name = question("Enter the environment variable name")
        value = question("Enter the environment variable value")
        vars[name] = value

#######################################################################################################################

def writeComputeWorkflow(resource_name, compute_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(),res_name+"_compute.json")
    print("  -> writing compute workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(compute_json,indent=4,sort_keys=True))
    f.close()

def writePeriodicComputeWorkflow(resource_name):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_compute_periodic"
    periodic_json["description"] = "Gather GLUE2 compute information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_compute.json"
    interval_str = question("How often should compute information be gathered (seconds)?","60")
    step_json["params"]["maximum_interval"] = int(interval_str)

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(),res_name+"_compute_periodic.json")
    print("  -> writing periodic compute workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(periodic_json,indent=4,sort_keys=True))
    f.close()

def writeActivityWorkflow(resource_name, activity_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(),res_name+"_activity.json")
    print("  -> writing activity workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(activity_json,indent=4,sort_keys=True))
    f.close()

def writeModulesWorkflow(resource_name, modules_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(),res_name+"_modules.json")
    print("  -> writing modules workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(modules_json,indent=4,sort_keys=True))
    f.close()

def writeExtModulesWorkflow(resource_name, extmodules_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(),res_name+"_extmodules.json")
    print("  -> writing extended modules workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(extmodules_json,indent=4,sort_keys=True))
    f.close()

def writeAbstractServicesWorkflow(resource_name, services_json):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getGlueWorkflowDir(),res_name+"_services.json")
    print("  -> writing abstract services workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(services_json,indent=4,sort_keys=True))
    f.close()

def writePeriodicModulesWorkflow(resource_name):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_modules_periodic"
    periodic_json["description"] = "Gather GLUE2 module information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_modules.json"
    interval_str = question("How often should module information be gathered (hours)?","1")
    step_json["params"]["maximum_interval"] = int(interval_str) * 60 * 60

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(),res_name+"_modules_periodic.json")
    print("  -> writing periodic modules workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(periodic_json,indent=4,sort_keys=True))
    f.close()

def writePeriodicExtModulesWorkflow(resource_name):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_extmodules_periodic"
    periodic_json["description"] = "Gather GLUE2 Extended module (Software) information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_extmodules.json"
    interval_str = question("How often should extended module information (XSEDE software) be gathered (hours)?","1")
    step_json["params"]["maximum_interval"] = int(interval_str) * 60 * 60

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(),res_name+"_extmodules_periodic.json")
    print("  -> writing periodic extended modules (software) workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(periodic_json,indent=4,sort_keys=True))
    f.close()

def writePeriodicAbstractServicesWorkflow(resource_name):
    res_name = resource_name.split(".")[0]
    periodic_json = {}
    periodic_json["name"] = res_name+"_services_periodic"
    periodic_json["description"] = "Gather GLUE2 AbstractService information periodically"
    periodic_json["steps"] = []

    step_json = {}
    step_json["name"] = "ipf.step.WorkflowStep"
    step_json["params"] = {}
    step_json["params"]["workflow"] = "glue2/"+res_name+"_services.json"
    interval_str = question("How often should AbstractService (XSEDE Services) information be gathered (hours)?","1")
    step_json["params"]["maximum_interval"] = int(interval_str) * 60 * 60

    periodic_json["steps"].append(step_json)

    path = os.path.join(getGlueWorkflowDir(),res_name+"_services_periodic.json")
    print("  -> writing periodic Abstract Services workflow to %s" % path)
    f = open(path,"w")
    f.write(json.dumps(periodic_json,indent=4,sort_keys=True))
    f.close()


#######################################################################################################################

def writeComputeInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(),"etc","ipf","init.d","ipf-"+res_name+"-glue2-compute")
    name = "%s_compute_periodic\n" % res_name
    writeInit(resource_name,module_names,env_vars,name,path)

def writeActivityInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(),"etc","ipf","init.d","ipf-"+res_name+"-glue2-activity")
    name = "%s_activity\n" % res_name
    writeInit(resource_name,module_names,env_vars,name,path)

def writeModulesInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(),"etc","ipf","init.d","ipf-"+res_name+"-glue2-modules")
    name = "%s_modules_periodic\n" % res_name
    writeInit(resource_name,module_names,env_vars,name,path)

def writeExtModulesInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(),"etc","ipf","init.d","ipf-"+res_name+"-glue2-extmodules")
    name = "%s_extmodules_periodic\n" % res_name
    writeInit(resource_name,module_names,env_vars,name,path)

def writeAbstractServicesInit(resource_name, module_names, env_vars):
    res_name = resource_name.split(".")[0]
    path = os.path.join(getBaseDir(),"etc","ipf","init.d","ipf-"+res_name+"-glue2-services")
    name = "%s_services_periodic\n" % res_name
    writeInit(resource_name,module_names,env_vars,name,path)

def writeInit(resource_name, module_names, env_vars, name, path):
    res_name = resource_name.split(".")[0]

    in_file = open(os.path.join(getBaseDir(),"etc","ipf","init.d","ipf-WORKFLOW"),"r")
    out_file = open(path,"w")
    for line in in_file:
        if line.startswith("NAME="):
            out_file.write("NAME=%s\n" % name)
        elif line.startswith("IPF_USER="):
            out_file.write("IPF_USER=%s\n" % getpass.getuser())
        elif line.startswith("export IPF_ETC_PATH="):
            out_file.write("export IPF_ETC_PATH=%s\n" % os.path.join(getBaseDir(),"etc/ipf"))
        elif line.startswith("export IPF_VAR_PATH="):
            out_file.write("export IPF_VAR_PATH=%s\n" % os.path.join(getBaseDir(),"var/ipf"))
        elif "modules" in line and module_names != None:
            out_file.write(line)
            out_file.write("source %s\n" % os.path.join(os.environ["MODULESHOME"],"init","bash"))
            for module_name in module_names:
                out_file.write("module load %s\n" % module_name)
        elif "environment variables" in line and len(env_vars) > 0:
            out_file.write(line)
            for name in env_vars:
                out_file.write("export %s=%s\n" % (name,env_vars[name]))
        else:
            out_file.write(line)
    in_file.close()
    out_file.close()

#######################################################################################################################

def getModulesType():
    return options("What modules system is used on this resource?",
                   ["lmod","modules"])

def getGlueWorkflowDir():
    return os.path.join(getWorkflowDir(),"glue2")

def getWorkflowDir():
    return os.path.join(getBaseDir(),"etc","ipf","workflow")

_base_dir = None
def getBaseDir():
    global _base_dir
    if _base_dir is not None:
        return _base_dir
    base_dir_opts = []
    if os.path.exists(os.path.join("/etc","ipf")):
        base_dir_opts.append("/")
    base_dir_opts.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base_dir_opts.append("other")
    _base_dir = options("Select base directory (files will be read/written to $BASE/etc/ipf, $BASE/var/ipf - "+
                        "  RPM install should use '/')",
                        base_dir_opts)
    if _base_dir == "other":
        _base_dir = question("Enter base directory")
    return _base_dir

def readWorkflowFile(path):
    f = open(path)
    text = f.read()
    f.close()
    return json.loads(text)

#######################################################################################################################

def question(text, default=None):
    print
    if default is None:
        answer = raw_input("%s: " % text)
        if answer == "":
            raise Exception("no input provided")
    else:
        answer = raw_input("%s (%s): " % (text,default))
        if answer == "":
            return default
    return answer

def options(text, opts, default=None):
    print
    if default is None:
        print("%s:" % text)
    else:
        print("%s (%s):" % (text,default))
    for i in range(len(opts)):
        print("  (%d) %s" % ((i+1),opts[i]))
    answer = raw_input(": ")
    if answer == "":
        if default is None:
            print("no options selected - pick a number")
            return options(text,opts,default)
        else:
            return default
    try:
        index = int(answer)
    except ValueError:
        print("enter a number")
        return options(text,opts,default)
    if index < 1 or index > len(opts):
        print("select an option between 1 and %d" % len(opts))
        return options(text,opts,default)
    return opts[index-1]

#######################################################################################################################

def testReadFile(path, print_warnings=True):
    if not os.path.exists(path):
        if print_warnings:
            print("  Warning: file %s doesn't exist" % path)
        return False
    if not os.access(path,os.R_OK):
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
    if not os.access(path,os.R_OK):
        if print_warnings:
            print("  Warning: directory %s can't be read by current user" % path)
        return False
    return True

#######################################################################################################################

if __name__ == "__main__":
    configure()
