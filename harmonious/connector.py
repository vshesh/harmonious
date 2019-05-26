from liblo import *
import time
import os
from pythonosc import udp_client
from datetime import datetime
import toolz as t
import toolz.curried as tc
import sys
import math
import simplejson as json
import requests

"""
py3tuio is a very basic implementation of a TUIO 1.x client written in Python 3 using pyliblo.
It is restricted to 2D surfaces and does not distinguish between different servers.
"""

class TuioClient(ServerThread):
    """
    the TuioClient processes TUIO/OSC messages and gives access
    to corresponding lists of TuioObjects
    """
    def __init__(self, port):
        ServerThread.__init__(self, port)
        self.tuio2DCursors = []
        self.tuio2DObjects = []
        self.tuio2DBlobs = []
        self._aliveObjectIds = set([])
        self._tuioObjectsNew = []
        self._tuioObjectsOld = []
        self.fseq = 0

    @make_method(None, None)
    def handleObjectMessage(self, path, args, types, src):
       """process the incoming TUIO/OSC messages"""
       messageType = args.pop(0)
       if messageType == "alive":
           self._aliveObjectIds = []
           for sessionId in args:
               self._aliveObjectIds.append(sessionId)
       elif messageType == "set":
           tuioObject = None
           if (path == "/tuio/2Dcur"):
               tuioObject = Tuio2DCursor(args)
               self._tuioObjectsOld = self.tuio2DCursors
           elif (path == "/tuio/2Dobj"):
               tuioObject = Tuio2DObject(args)
               self._tuioObjectsOld = self.tuio2DObjects
           elif (path == "/tuio/2Dblb"):
               tuioObject = Tuio2DBlob(args)
               self._tuioObjectsOld = self.tuio2DBlobs
           if (tuioObject):
               self._tuioObjectsNew.append(tuioObject)
               self._aliveObjectIds.remove(tuioObject.sessionId)
       elif messageType == "fseq":
           if ((args[0] == -1) | (self.fseq < args[0])):
               self.fseq = args[0]
               # add all objects which didn't change but are still alive
               for o in self._tuioObjectsOld:
                   if (o.sessionId in self._aliveObjectIds):
                       self._tuioObjectsNew.append(o)
               if (path == "/tuio/2Dcur"):
                   self.tuio2DCursors = self._tuioObjectsNew
               elif (path == "/tuio/2Dobj"):
                   self.tuio2DObjects = self._tuioObjectsNew
               elif (path == "/tuio/2Dblb"):
                   self.tuio2DBlob = self._tuioObjectsNew
           self._tuioObjectsNew = []

class TuioObject(object):
    """this represents a TUIO object"""
    def __init__(self, args, argsLength):
        if (len(args) != argsLength):
            raise ValueError("TUIO Message: wrong number of arguments")

class Tuio2DCursor(TuioObject):
    """this represents a TUIO 2D cursor"""
    def __init__(self, args):
        super(Tuio2DCursor, self).__init__(args, 6)
        self.sessionId, self.x, self.y, self.xVelocity, self.yVelocity, self.acceleration = args[0:6]

class Tuio2DObject(TuioObject):
    """this represents a TUIO 2D object"""
    def __init__(self, args):
        super(Tuio2DObject, self).__init__(args, 10)
        self.sessionId, self.markerId, self.x, self.y, self.angle, self.xVelocity, self.yVelocity, self.rotationSpeed, self.acceleration, self.rotationAcceleration = args[0:10]

class Tuio2DBlob(TuioObject):
    """this represents a TUIO 2D blob"""
    def __init__(self, args):
        super(Tuio2DBlob, self).__init__(args, 12)
        self.sessionId, self.x, self.y, self.angle, self.width, self.height, self.area, self.xVelocity, self.yVelocity, self.rotationSpeed, self.acceleration, self.rotationAcceleration = args[0:12]




# ^ Everything above here was taken from a github gist: https://github.com/arminbw/py3tuio/blob/master/py3tuio.py

def make_debouncer(sender, i=0):
    """
    After writing this I realized some of this functionality was already above, but not all of it.

    :param sender:
    :return:
    """
    d = {}
    def debounce(objects):
        changed = False
        for o in objects:
            if o.markerId not in d or d[o.markerId][3] != round(o.angle) % 6:
                changed = True
            d[o.markerId] = (datetime.now(), o.x, o.y, round(o.angle) % 6)
        
        old = t.valfilter(lambda x: (datetime.now() - x[0]).seconds > 0.5, d)
        for o in old:
            d.pop(o)
        
        # at this position - either we changed, or we lost a tower
        if changed or len(old) > 0:
          if len(d) == 0:
            # no towers at this position
            o = next(iter(old))
            sender(json.dumps({i: {}}))
          else:
            sender( json.dumps({i: {k:[v[-2], v[-1]] for k,v in d.items()}}) )
    return debounce


def demo(NUM_PADS):
    try:
        client = TuioClient(3333)
        
        # 4 senders for four positions independently.
        debounce_senders = [make_debouncer(lambda x: print(x, flush=True), i) for i in range(NUM_PADS)]
        for i in range(NUM_PADS):
          print(json.dumps({i: {}}), flush=True)
    except ServerError as err:
        sys.exit(str(err))
    client.start()
    while (True):
        time.sleep(0.1)
        try:
          for i in range(len(debounce_senders)):
            # send to corresponding cache if the position has changed.
            debounce_senders[i](o for o in client.tuio2DObjects if math.floor(NUM_PADS*o.x) == NUM_PADS-1-i)
            
        except:
            client.stop()
            sys.exit()

if __name__ == '__main__':
  demo(int(sys.argv[1]))
