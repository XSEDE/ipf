#!/usr/bin/env python

import getpass
import optparse
import os
import signal
import ssl
import sys
import time

import amqp

#######################################################################################################################

keep_running = True

def sigHandler(signal, frame):
    global keep_running
    keep_running = False

signal.signal(signal.SIGINT, sigHandler)
            
#######################################################################################################################

def parser():
    usage = "Usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-s","--server",default="localhost",dest="server",
                      help="the server running the messaging service")

    parser.add_option("-u","--user",dest="user",
                      help="the user to authenticate as")
    parser.add_option("-p","--password",dest="password",
                      help="the password to use to authenticate")
    parser.add_option("-P","--askpass",dest="ask_pass",action="store_true",
                      help="ask for the password to use to authenticate on stdin")
    parser.add_option("-k","--key",dest="keyfile",
                      help="the file containing a key")
    parser.add_option("-c","--cert",dest="certfile",
                      help="the file containing a certificate")
    parser.add_option("-a","--cacert",dest="ca_certfile",
                      help="the file containing the CA certificates")
    
    parser.add_option("-v","--vhost",default="/",dest="vhost",
                      help="the virtual host in the messaging service to connect to")
    parser.add_option("-e","--exchange",default="amq.topic",dest="exchange",
                      help="an exchange in the virtual host to publish or subscribe to")
    return parser

#######################################################################################################################

if os.path.exists(os.path.join("etc","ipf","xsede","ca_certs.pem")):
    ca_cert_file = (os.path.join("etc","ipf","xsede","ca_certs.pem"))
elif os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),"etc","ipf","xsede","ca_certs.pem")):
    ca_cert_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"etc","ipf","xsede","ca_certs.pem")

def connect(options):
    # port 5671 is for SSL, port 5672 is for TCP
    if options.keyfile is not None or options.certfile is not None:
        if options.keyfile is None:
            print("you must specify a key file for user with your cert file")
            sys.exit(1)
        if options.certfile is None:
            print("you must specify a cert file for user with your key file")
            sys.exit(1)
        if options.ca_certfile is None:
            print("you must specify a ca_certs file")
            sys.exit(1)
        print("connecting to %s:5671 with certificate and key" % options.server)

        return amqp.Connection(host="%s:%d" % (options.server,5671),
                               virtual_host=options.vhost,
                               ssl={"keyfile":options.keyfile,
                                    "certfile":options.certfile,
                                    "cert_reqs":ssl.CERT_REQUIRED,
                                    "ca_certs":options.ca_certfile},
                               heartbeat=60)
    if options.password is not None and options.ask_pass:
        print("don't specify -p and -P")
        sys.exit(1)
    if options.password is not None or options.ask_pass:
        if options.user is None:
            print("you must specify a user if you provide a password")
            sys.exit(1)
    if options.user is not None:
        if options.password is None:
            if options.ask_pass:
                options.password = getpass.getpass("password for %s:" % options.user)
            else:
                print("you must specify a password along with a user")
                sys.exit(1)
        if options.ca_certfile is not None:
            print("connecting over SSL to %s:5671 with username and password" % options.server)
            return amqp.Connection(host="%s:%d" % (options.server,5671),
                                   userid=options.user,
                                   password=options.password,
                                   virtual_host=options.vhost,
                                   ssl={"cert_reqs":ssl.CERT_REQUIRED,
                                        "ca_certs":options.ca_certfile},
                                   heartbeat=60)
        else:
            print("connecting over TCP to %s:5672 with username and password" % options.server)
            return amqp.Connection(host="%s:%d" % (options.server,5672),
                                   userid=options.user,
                                   password=options.password,
                                   virtual_host=options.vhost,
                                   heartbeat=60)
    else:
        print("connecting to %s:5672 anonymously" % options.server)
        return amqp.Connection(host="%s:%d" % (options.server,5672),
                               virtual_host=options.vhost,
                               heartbeat=60)

#######################################################################################################################

def subscribe(channel, exchange, filter):
    print("subscribing to exchange %s for messages matching '%s'" % (exchange,filter))
    declare_ok = channel.queue_declare()
    queue = declare_ok.queue
    channel.queue_bind(queue,exchange,filter)
    consumer_tag = channel.basic_consume(queue,callback=incoming)

def incoming(message):
    routing_key = message.delivery_info["routing_key"]
    print("received: %s" % message.body)

#######################################################################################################################

if __name__ == "__main__":
    parser = parser()
    parser.add_option("-f","--filter",default="#",dest="filter",
                      help="filter for message routing keys")
    (options, args) = parser.parse_args()

    conn = connect(options)
    channel = conn.channel()

    subscribe(channel,options.exchange,options.filter)

    print("press ctrl-C to exit")
    while keep_running:
        try:
            channel.wait()
        except:
            pass
    print("shutting down")
    channel.close()
    conn.close()

#######################################################################################################################
