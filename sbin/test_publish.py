#!/bin/env python

from ipf.agent.amqp import *
from ipf.document import Document

public_doc = Document()
public_doc.id = "ranger.tacc.teragrid.org"
public_doc.type = "glue2_system"
public_doc.content_type = "text/xml"
f = open("/share/home/00415/wsmith/glue2/var/glue2_public.xml","r")
public_doc._body = f.read()
f.close()

args = {"publish_amqp.vhost" : "teragrid_public",
        "publish_amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run([public_doc])

private_doc = Document()
private_doc.id = "ranger.tacc.teragrid.org"
private_doc.type = "glue2_system"
private_doc.content_type = "text/xml"
f = open("/share/home/00415/wsmith/glue2/var/glue2_private.xml","r")
private_doc._body = f.read()
f.close()

args = {"publish_amqp.vhost" : "teragrid_private",
        "publish_amqp.exchange" : "glue2"}
AmqpPublishingAgent(args).run([private_doc])
