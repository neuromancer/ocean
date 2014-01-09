
from signal import SIGTRAP, SIGSEGV
from Event import CallGraph

class Stats:
  def __init__(self, events):
    #self.original_events = tuple(map(str, events))
    self.count = dict()
    self.keys = set()

    #for event in self.original_events:
    #    print event

    CallGraph(events)
    exit(0)

    self.keys.add(self.original_events)
    self.fields = []

  #def __IncCount(self, input, offset, mtype, byte, data):
  #
  #  self.keys.add((input, mtype, offset))
  #  self.count[(input, mtype, offset, byte)] = data

  def AddData(self, delta, events):

    #if self.fields == []:
    #  self.fields = list(delta.keys())

    #print str(events)
    events = tuple(map(str, events))
    if "Crash@" in events[-1] and not (events in self.keys):

      self.keys.add(events)
      print "Adding:"
      for event in events:
        print event

    #print str(events[0])
       #status = events[-1]
    #if "Crash@" in events[-1] and events <> self.original_events:
    #  print "Adding:"
    #  for event in events:
    #    print event
    #  self.__IncCount(delta["iname"], delta["mtype"], delta["aoffset"], delta["byte"], (delta, list(events)))
    #else:
    #  print "Pass"


  """
  def Compute(self):

    r = []#[list(self.fields)+["status"]]

    for (input, mtype, offset) in self.keys:
      i = 0
      for byte in range(256):
        if (input, mtype, offset, byte) in self.count:
          i += 1

      prob = 1.0 - float(i)/256

      if prob <= 0.2 or i == 0:
        pass
        #print input, offset, "is irrelevant!"
      else:

        for byte in range(256):
          if (input, mtype, offset, byte) in self.count:
            delta, events = self.count[(input, mtype, offset, byte)]
            r.append(delta.values()+[' '.join(events)]) #print (input, offset, byte), "is relevant with prob", str(prob), "!"

    return r
    #print self.keys
  """
