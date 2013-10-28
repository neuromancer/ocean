
from signal import SIGTRAP, SIGSEGV
from Event import Exit, Signal

class Stats:
  def __init__(self):
    self.count = dict()
    self.keys = set()
    self.fields = []

  def __IncCount(self, input, offset, byte, data):

    self.keys.add((input, offset))
    self.count[(input, offset, byte)] = data

  def AddData(self, delta, events):

    if self.fields == []:
      self.fields = list(delta.keys())

    #print str(events[0])
    events = map(str, events)
    #status = events[-1]
    if "Crash@" in events[-1]:
      self.__IncCount(delta["iname"], delta["aoffset"], delta["byte"], (delta, list(events)))


  def Compute(self):

    r = []#[list(self.fields)+["status"]]

    for (input, offset) in self.keys:
      i = 0
      for byte in range(256):
        if (input, offset, byte) in self.count:
          i+=1

      prob = 1.0 - float(i)/256

      if prob <= 0.2 or i == 0:
        pass
        #print input, offset, "is irrelevant!"
      else:

        for byte in range(256):
          if (input, offset, byte) in self.count:
            delta, events = self.count[(input, offset, byte)]
            r.append(delta.values()+[' '.join(events)]) #print (input, offset, byte), "is relevant with prob", str(prob), "!"

    return r
    #print self.keys

