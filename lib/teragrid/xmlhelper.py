
import datetime
import math
import re
import xml.dom
import time

from ipf.error import *

def xmlToEpoch(str):

    toks = str.split('T')
    if len(toks) < 2:
        raise ParseError("invalid date time string: 'T' does not appear")
    if len(toks) > 2:
        raise ParseError("invalid date time string: 'T' appears more than once")

    date = toks[0]
    timetz = toks[1]

    toks = date.split('-')
    if len(toks) != 3:
        raise ParseError("invalid date part - exactly 2 dashes not found")

    year = int(toks[0])
    month = int(toks[1])
    day = int(toks[2])

    if timetz.find("-") >= 0:
        toks = timetz.split('-')
        timePart = toks[0]
        tzPart = toks[1]
        tzSignMult = -1
    elif timetz.find("+") >= 0:
        toks = timetz.split('+')
        timePart = toks[0]
        tzPart = toks[1]
        tzSignMult = 1
    elif timetz.find("Z") >= 0:
        timePart = timetz[:len(timetz)-1]
        tzPart = None
    else:
        timePart = timetz
        tzPart = None

    toks = timePart.split(':')
    if len(toks) != 3:
        raise ParseError("invalid time part: ':' doesn't appear exactly twice")
    hour = int(toks[0])
    minute = int(toks[1])
    second = float(toks[2])
    millisecond = int((second - int(second)) * 1000000)

    if tzPart != None:
        toks = tzPart.split(':')
        if len(toks) != 2:
            raise ParseError("invalid time zone: ':' doesn't appear exactly once")
        tzHour = int(toks[0])
        tzMinute = int(toks[1])
        offset = tzSignMult * (tzHour * 60 + tzMinute) * 60
    else:
        offset = 0

    dt = datetime.datetime(year,month,day,hour,minute,int(second),millisecond,tzoffset(offset))
    localEpoch = time.mktime(dt.timetuple())
    
    # mktime() returns seconds since the local epoch
    # so convert to seconds since the UTC epoch (like time.time() returns)
    return localEpoch - time.timezone

def epochToXml(epoch):

    #dt = datetime.datetime.fromtimestamp(epoch,tzoffset(0))
    #print "offset in hours: " + str(time.timezone / 60 / 60)
    # time.timezone is an hour too much on my system
    #dt = datetime.datetime.fromtimestamp(epoch,tzoffset(-time.timezone))
    #dt = datetime.datetime.fromtimestamp(epoch,localtzoffset())
    #dt = datetime.datetime.fromtimestamp(epoch)
    #dt = datetime.datetime.utcfromtimestamp(epoch)
    #return dt.isoformat() # not quite right

    #dt = datetime.datetime.fromtimestamp(epoch,localtzoffset())
    #dt = datetime.datetime.fromtimestamp(epoch)
    dt = datetime.datetime.utcfromtimestamp(epoch)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def xmlDurationToSecs(duration):
    # P1Y2M3DT10H30M12.3S
    if duration[0] != 'P':
        raise ParseError("first character of duration string is not a 'P'")

    number = "";
    durationSecs = 0;
    inDate = True;
    for i in range(1,len(duration)):
        if re.compile("[0-9.]").match(str(duration[i])) != None:
            number = number + duration[i]
        else:
            if duration[i] == 'Y':
                if int(number) != 0:
                    print "durations greater than a year are not supported, ignoring"
            elif duration[i] == 'M':
                if inDate:
                    print "durations greater than a month are not supported, ignoring"
                else:
                    durationSecs = durationSecs + int(number) * 60
            elif duration[i] == 'D':
                durationSecs = durationSecs + int(number) * 24 * 60 * 60
            elif duration[i] == 'T':
                inDate = False
            elif duration[i] == 'H':
                durationSecs = durationSecs + int(number) * 60 * 60
            elif duration[i] == 'S':
                durationSecs = durationSecs + float(number)
            else:
                raise ParseError("unexpected character in duration: " + str(duration[i]))
            number = ""

    return durationSecs

def secsToXmlDuration(durationSecs):

    days = math.floor(durationSecs / (24 * 60 * 60))
    durationSecs = durationSecs - days * 24 * 60 * 60
    hours = math.floor(durationSecs / (60 * 60))
    durationSecs = durationSecs - hours * 60 * 60
    minutes = math.floor(durationSecs / 60)
    secs = durationSecs - minutes * 60

    durStr = "T"
    if days > 0:
        durStr = durStr + str(days) + "D"
    if hours > 0:
        durStr = durStr + str(hours) + "H"
    if minutes > 0:
        durStr = durStr + str(minutes) + "M"
    if secs > 0:
        durStr = durStr + str(secs) + "S"
    return durStr

def getFirstChildElement(node):
    for node in node.childNodes:
        if node.nodeType == xml.dom.Node.ELEMENT_NODE:
            return node
