#!/usr/bin/env python

from ipf.agent.file import *
from ipf.agent.amqp import *
#from ipf.agent.rest import *
from teragrid.glue2.cobalt import *
from teragrid.glue2.gram_endpoint import *
from teragrid.glue2.entities import *
from teragrid.glue2.tg_envelope import *

# configuration information can be set in glue2-x.x.x/etc/agent.cfg
# or in arguments passed to the agent constructors below

activities = CobaltJobsAgent().run()

private_doc = TeraGridGlue2Agent().run(EntitiesAgent().run(activities))

shares = CobaltQueuesAgent().run(activities)
endpoints = GramEndpointsAgent().run()
service = CobaltComputingServiceAgent().run(shares + endpoints)
exec_envs = CobaltExecutionEnvironmentsAgent().run()
manager = CobaltComputingManagerAgent().run(shares + exec_envs + service)

public_doc = TeraGridGlue2Agent().run(EntitiesAgent().run(service +
                                                          endpoints +
                                                          shares +
                                                          manager +
                                                          exec_envs))

# if using WS-MDS to publish, write the documents to files
args = {"filepub.file_name" : "var/glue2_private.xml"}
FilePublishingAgent(args).run(private_doc)
args = {"filepub.file_name" : "var/glue2_public.xml"}
FilePublishingAgent(args).run(public_doc)

args = {"amqp.vhost" : "teragrid_public",
        "amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run(public_doc)

args = {"amqp.vhost" : "teragrid_private",
        "amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run(private_doc)

##############################################################################################################

