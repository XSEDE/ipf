#!/usr/bin/env python

from ipf.agent.file import *
from ipf.agent.amqp import *
#from ipf.agent.rest import *
from teragrid.glue2.sge import *
from teragrid.glue2.sge.tacc import *
from teragrid.glue2.gram_endpoint import *
from teragrid.glue2.entities import *
from teragrid.glue2.tg_envelope import *

# configuration information can be set in glue2-x.x.x/etc/agent.cfg
# or in arguments passed to the agent constructors below

activities = SgeJobsAgent().run()

private_doc = TeraGridGlue2Agent().run(EntitiesAgent().run(activities))

shares = TaccSgeQueuesAgent().run(activities)
endpoints = GramEndpointsAgent().run()
service = SgeComputingServiceAgent().run(shares + endpoints)
exec_envs = SgeExecutionEnvironmentsAgent().run()
manager = SgeComputingManagerAgent().run(shares + exec_envs + service)

public_doc = TeraGridGlue2Agent().run(EntitiesAgent().run(service +
                                                          endpoints +
                                                          shares +
                                                          manager +
                                                          exec_envs))

# if using WS-MDS to publish, write the documents to files
args = {"publish_file.file_name" : "var/glue2_private.xml"}
FilePublishingAgent(args).run(private_doc)
args = {"publish_file.file_name" : "var/glue2_public.xml"}
FilePublishingAgent(args).run(public_doc)

args = {"publish_amqp.vhost" : "teragrid_public",
        "publish_amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run(public_doc)

args = {"publish_amqp.vhost" : "teragrid_private",
        "publish_amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run(private_doc)

##############################################################################################################

