
import datetime
import time

#######################################################################################################################

class tzoffset(datetime.tzinfo):

    def __init__(self, offset=0):
        self._offset = datetime.timedelta(seconds=offset)
    
    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        #return self._dstoffset
        return datetime.timedelta(0)

    def tzname(self, dt):
        return self._name

#######################################################################################################################

class localtzoffset(datetime.tzinfo):

    def __init__(self):
        self.stdOffset = datetime.timedelta(seconds=-time.timezone)
        if time.daylight:
            self.dstOffset = datetime.timedelta(seconds=-time.altzone)
        else:
            self.dstOffset = self.stdOffset
        self.dstDiff = self.dstOffset - self.stdOffset
    
    def utcoffset(self, dt):
        if self._isdst(dt):
            return self.dstOffset
        else:
            return self.stdOffset

    def dst(self, dt):
        if self._isdst(dt):
            return self.dstDiff
        else:
            return datetime.timedelta(0)

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        epoch = time.mktime(tt)
        tt = time.localtime(epoch)
        return tt.tm_isdst > 0

    def tzname(self, dt):
        return time.tzname

#######################################################################################################################

def epochToDateTime(epoch, tz=tzoffset(0)):
    if epoch is None:
        return None
    return datetime.datetime.fromtimestamp(epoch,tz)

def epochToText(epoch, tz=tzoffset(0)):
    if epoch is None:
        return None
    #return dateTimeToText(datetime.datetime.utcfromtimestamp(epoch))
    return dateTimeToText(datetime.datetime.fromtimestamp(epoch,tz))

def dateTimeToText(dt):
    if dt is None:
        return None
    if dt.utcoffset():
        dt = dt - dt.utcoffset()
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def textToEpoch(text):
    if text is None:
        return None
    dt = textToDateTime(text)
    return dateTimeToEpoch(dt)
    
def textToDateTime(text):
    if text is None:
        return None
    return datetime.datetime.strptime(text,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tzoffset(0))

def dateTimeToEpoch(dt):
    if dt is None:
        return None
    if dt.utcoffset():
        udt = dt - dt.utcoffset()
    else:
        udt = dt
    return time.mktime(udt.timetuple())

#######################################################################################################################

def test(cur):
    print("current time: "+cur.isoformat())

    cur_text = dateTimeToText(cur)
    print("  %s" % cur_text)

    dt = textToDateTime(cur_text)
    print("  %s" % dt.isoformat())

    print("  %f" % textToEpoch(cur_text))

    print("  %f" % dateTimeToEpoch(cur))

if __name__ == "__main__":
    #test(datetime.datetime.now())  # no time zone information
    test(datetime.datetime.utcnow())  # no time zone information - assume UTC
    test(datetime.datetime.now(tzoffset(0)))
    test(datetime.datetime.now(localtzoffset()))
