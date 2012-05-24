#!/usr/bin/env python

from ipf.agent.file import *
from ipf.agent.amqp import *
from teragrid.glue2.sge import *
from teragrid.glue2.sge.tacc import *
from teragrid.glue2.gram_endpoint import *
from teragrid.glue2.entities import *
from teragrid.glue2.tg_envelope import *

# configuration information is specified in glue2-x.y.z/etc/agent.cfg
#   (see glue2-x.y.z/etc/example/agent-<resource>.cfg for examples)

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

# by default, publish via AMQP messaging
args = {"publish_amqp.vhost" : "teragrid_public",
        "publish_amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run(public_doc)
args = {"publish_amqp.vhost" : "teragrid_private",
        "publish_amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run(private_doc)

# if using WS-MDS to publish, write the documents to files
#args = {"publish_file.file_name" : "var/glue2_private.xml"}
#FilePublishingAgent(args).run(MdsEnvelopeAgent().run(private_doc))
#args = {"publish_file.file_name" : "var/glue2_public.xml"}
#FilePublishingAgent(args).run(MdsEnvelopeAgent().run(public_doc))
