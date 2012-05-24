#!/bin/env python

import commands
import logging
import multiprocessing
import os
import random
import re
import shutil
from ssl import CERT_REQUIRED
import sys
import time
from xml.dom.minidom import parseString
import ConfigParser

from pika.adapters import SelectConnection
from pika.connection import ConnectionParameters
from pika.credentials import *
import pika.exceptions
from pika import BasicProperties

from teragrid.glue2.execution_environment import ExecutionEnvironment
from teragrid.glue2.computing_activity import ComputingActivity

##############################################################################################################

home_dir = os.environ.get("GLUE2_HOME")
if home_dir == None:
    print "GLUE2_HOME environment variable not set"
    sys.exit(1)

logger = logging.getLogger("subscribe")
handler = logging.StreamHandler()
#formatter = logging.Formatter("%(asctime)s %(message)s")
formatter = logging.Formatter("%(levelname)s: %(message)s")
#formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

##############################################################################################################

class Subscribe(multiprocessing.Process):
    def __init__(self, vhost="teragrid_public", exchange="glue2", routing_key=None, verify=True):
        multiprocessing.Process.__init__(self)
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(home_dir+"/etc/agent.cfg")
        self.vhost = vhost
        self.exchange = exchange
        self.routing_key = routing_key
        if self.routing_key == None:
            self.routing_key = self._getResourceName()
        self.verify = verify

    def _getResourceName(self):
        try:
            return self.config.get("teragrid","resource_name")
        except ConfigParser.Error:
            pass
        tg_whereami = "tgwhereami"
        try:
            tg_whereami = self.config.get("teragrid","tgwhereami")
        except ConfigParser.Error:
            pass
        (status, output) = commands.getstatusoutput(tg_whereami)
        if status == 0:
            return output
        logger.error("could not determine resource name")
        sys.exit(1)

    def run(self):
        self._configureBrokers()
        self._connect()
        if self.connection == None:
            return

        self.connection.ioloop.start()
        logger.info("exiting")

    def _configureBrokers(self):
        brokers_str = self.config.get("publish_amqp","broker")

        self.brokers = []
        for hostport in brokers_str.split():
            toks = hostport.split(":")
            self.brokers.append([toks[0],int(toks[1])])
        random.shuffle(self.brokers)

    def _connect(self):
        if len(self.brokers) == 0:
            raise Exception("failed to connect to any of the specified amqp brokers")

        (host,port) = self.brokers.pop()
        creds = ExternalCredentials()
        parameters = ConnectionParameters(host,port,self.vhost,creds,ssl=True,ssl_options=self._getSslOptions())
        try:
            self.connection = SelectConnection(parameters,self.onConnected)
            logger.debug("connected to %s on %s:%s" % (self.vhost,host,port))
        except pika.exceptions.AMQPConnectionError, e:
            logger.warn("failed to connect to %s:%s: %s" % (host,port,str(e)))
            self._connect()

    def _getSslOptions(self):
        cacerts_filename = os.path.join(home_dir,"etc","cacerts.pem")
        self._generateCaCertsFile(cacerts_filename)

        try:
            key_file = self.config.get("publish_amqp","key")
        except ConfigParser.Error:
            key_file = "/etc/grid-security/hostkey.pem"

        try:
            cert_file = self.config.get("publish_amqp","certificate")
        except ConfigParser.Error:
            try:
                cert_file = self.config.get("globus","host_certificate")
            except ConfigParser.Error:
                cert_file = "/etc/grid-security/hostcert.pem"

        return {"keyfile": key_file,
                "certfile": cert_file,
                "cert_reqs": CERT_REQUIRED,
                "ca_certs": cacerts_filename}
        
    def _generateCaCertsFile(self, cacerts_filename):
        if os.path.exists(cacerts_filename):
            if os.path.getmtime(cacerts_filename) > time.time() - 7*24*60*60:
                return

        try:
            cadir = self.config.get("publish_amqp","ca_certificates_directory")
        except ConfigParser.Error:
            try:
                cadir = self.config.get("globus","ca_certificates_directory")
            except ConfigParser.Error:
                cadir = "/etc/grid-security/certificates"

        listing = os.listdir(cadir)
        listing.sort()
        file = open(cacerts_filename,"w")
        for file_name in listing:
            if file_name.endswith(".0"):
                shutil.copyfileobj(open(os.path.join(cadir,file_name),"r"), file)
        file.close()

    def onConnected(self, conn):
        self.connection.channel(self.onChannelOpen)

    def onChannelOpen(self, ch):
        self.channel = ch
        self.channel.add_on_close_callback(self.onClose)

        result = self.channel.queue_declare(self.onQueueDeclare,exclusive=True)

    def onQueueDeclare(self, method):
        self.queue = method.method.queue
        #print("binding queue %s to exchange %s" % (self.queue,self.exchange))
        #self.channel.queue_bind(queue=self.queue,exchange=self.exchange,callback=self.on_queue_bound)
        #self.channel.queue_bind(queue=self.queue,exchange=self.exchange,routing_key="#",callback=self.on_queue_bound)
        self.channel.queue_bind(queue=self.queue,
                                exchange=self.exchange,
                                routing_key=self.routing_key,
                                callback=self.onQueueBound)

    def onQueueBound(self, method):
        logger.info("consuming from exchange %s in vhost %s" % (self.exchange,self.vhost))
        self.channel.basic_consume(self.callback,self.queue)

    def onClose(self, reply_code, reply_text):
        logger.info("session closed ("+str(reply_code)+"): "+reply_text)
        if reply_code != 200:
            logger.warn(str(reply_code)+": "+reply_text)
            self.error_msg = reply_text

    def callback(self, channel, method, header, body):
        #print(body)
        m = re.search("<ResourceID>(\S+)</ResourceID>",body)
        if self.vhost == "teragrid_public":
            logger.info(">>>>> received glue2 system description message about %s <<<<<" % (m.group(1)))
            if self.verify:
                VerifyPublic().verify(body)
        else:
            logger.info(">>>>> received glue2 jobs message about %s <<<<<<" % (m.group(1)))
            if self.verify:
                VerifyPrivate().verify(body)
            
##############################################################################################################

class Verify(object):
    def __init__(self):
        pass

    def verifyResourceId(self, glue2_element):
        for node in glue2_element.childNodes:
            if node.localName == "ResourceID":
                logger.info("verify resource id is correct: "+node.childNodes[0].data)
                return
        logger.error("resource id not found in document")

    def verifySiteId(self, glue2_element):
        for node in glue2_element.childNodes:
            if node.localName == "SiteID":
                logger.info("verify site id is correct: "+node.childNodes[0].data)
                return
        logger.error("site id not found in document")

##############################################################################################################

class VerifyPublic(Verify):
    def __init__(self):
        pass

    def verify(self, xml):
        dom = parseString(xml)
        glue2_element = dom.childNodes[0]

        self.verifyResourceId(glue2_element)
        self.verifySiteId(glue2_element)

        for node in glue2_element.childNodes:
            if node.localName == "Entities":
                self.verifyEndpoints(node)
                self.verifyShares(node)
                self.verifyExecutionEnvironments(node)

    def verifyEndpoints(self, entities_element):
        num_endpoints = 0
        for node in entities_element.childNodes:
            if node.localName == "ComputingEndpoint":
                num_endpoints += 1
                self.verifyEndpoint(node)
        if num_endpoints == 0:
            logger.warn("no computing endpoints found")
            logger.warn("  if you have GRAM endpoints on your system, check that core_kit_directory in etc/agent.cfg points to your TeraGrid CTSS core kit directory")
        else:
            logger.info("(missing endpoints may be caused by missing registrations in the CTSS remote compute kit)")

    def verifyEndpoint(self, endpoint_element):
        #print("------------------------------------------")
        #print(endpoint_element.toxml())
        name = ""
        url = ""
        impl_name = ""
        impl_version = ""
        for node in endpoint_element.childNodes:
            if node.localName == "Name":
                name = node.childNodes[0].data
            if node.localName == "URL":
                url = node.childNodes[0].data
            if node.localName == "ImplementationName":
                impl_name = node.childNodes[0].data
            if node.localName == "ImplementationVersion":
                impl_version = node.childNodes[0].data
        logger.info("verify endpoint %s is correct:" % (name))
        logger.info("  version %s of %s" % (impl_version,impl_name))
        logger.info("  url %s" % (url))

    def verifyShares(self, entities_element):
        num_shares = 0
        logger.info("verify that the following queues should be advertised:")
        for node in entities_element.childNodes:
            if node.localName == "ComputingShare":
                num_shares += 1
                self.verifyShare(node)
        if num_shares == 0:
            logger.error("no computing shares found")
        logger.info("(queues can be filtered using the queues property in etc/agent.cfg)")

    def verifyShare(self, share_element):
        name = ""
        for node in share_element.childNodes:
            if node.localName == "Name":
                name = node.childNodes[0].data
        logger.info("    %s" % (name))

    def verifyExecutionEnvironments(self, entities_element):
        envs = []
        for node in entities_element.childNodes:
            if node.localName == "ExecutionEnvironment":
                envs.append(self.getExecEnv(node))
        if len(envs) == 0:
            logger.error("no execution environments found")
        for env in envs:
            logger.info("verify %d nodes (%d used, %d unavailable) with:" %
                        (env.TotalInstances,env.UsedInstances,env.UnavailableInstances))
            logger.info("  operating system: %s %s" % (env.OSName,env.OSVersion))
            logger.info("  %d cores" % (env.LogicalCPUs))
            if env.MainMemorySize != None:
                logger.info("  %d MB of memory" % (env.MainMemorySize))
        logger.info("(nodes can be filtered based on their properties using the nodes property in etc/agent.cfg)")

    def getExecEnv(self, env_element):
        env = ExecutionEnvironment()
        for node in env_element.childNodes:
            if node.localName == "Name":
                env.Name = node.childNodes[0].data
            if node.localName == "Platform":
                env.Platform = node.childNodes[0].data
            if node.localName == "TotalInstances":
                env.TotalInstances = int(node.childNodes[0].data)
            if node.localName == "UsedInstances":
                env.UsedInstances = int(node.childNodes[0].data)
            if node.localName == "UnavailableInstances":
                env.UnavailableInstances = int(node.childNodes[0].data)
            if node.localName == "PhysicalCPUs":
                env.PhysicalCPUs = int(node.childNodes[0].data)
            if node.localName == "LogicalCPUs":
                env.LogicalCPUs = int(node.childNodes[0].data)
            if node.localName == "MainMemorySize":
                env.MainMemorySize = int(node.childNodes[0].data)
            if node.localName == "OSName":
                env.OSName = node.childNodes[0].data
            if node.localName == "OSVersion":
                env.OSVersion = node.childNodes[0].data
        return env
    
##############################################################################################################

class VerifyPrivate(Verify):
    def __init__(self):
        pass

    def verify(self, xml):
        dom = parseString(xml)
        glue2_element = dom.childNodes[0]

        self.verifyResourceId(glue2_element)
        self.verifySiteId(glue2_element)

        for node in glue2_element.childNodes:
            if node.localName == "Entities":
                self.verifyActivities(node)

    def verifyActivities(self, entities_element):
        jobs = []
        for node in entities_element.childNodes:
            if node.localName == "ComputingActivity":
                jobs.append(self.getActivity(node))
        if len(jobs) == 0:
            logger.error("no jobs found")
            return

        logger.info("verify %d jobs being managed:" % (len(jobs)))
        num_running = 0
        num_pending = 0
        num_other = 0
        used_slots = 0
        for job in jobs:
            if job.State == "teragrid:running":
                num_running += 1
                used_slots += job.RequestedSlots
            elif job.State == "teragrid:pending":
                num_pending += 1
            else:
                num_other += 1
        logger.info("  %d running, %d pending, %d other" % (num_running,num_pending,num_other))
        logger.info("  running jobs are using %d slots" % (used_slots))
        queues = set()
        for job in jobs:
            if job.Queue != None:
                queues.add(job.Queue)
        logger.info("  verify jobs are in the following queues:")
        for queue in queues:
            logger.info("    %s" % (queue))
        logger.info("(jobs can be filtered based on their queue using the queues property in etc/agent.cfg)")

    def getActivity(self, env_element):
        job = ComputingActivity()
        for node in env_element.childNodes:
            if node.localName == "State":
                job.State = node.childNodes[0].data
            if node.localName == "RequestedSlots":
                job.RequestedSlots = int(node.childNodes[0].data)
            if node.localName == "Queue":
                job.Queue = node.childNodes[0].data
        return job

##############################################################################################################

def usage():
    print("usage: subscribe.py [--verify]")
    sys.exit(1)

if __name__ == "__main__":

    if len(sys.argv) > 2:
        usage()

    verify = True
    if len(sys.argv) == 2:
        if sys.argv[1] == "--noverify":
            verify = False
        else:
            usage()

    pub = Subscribe("teragrid_public",verify=verify)
    pub.start()
    priv = Subscribe("teragrid_private",verify=verify)
    priv.start()

    pub.join()
    priv.join()
