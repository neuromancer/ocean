
from signal import SIGTRAP, SIGSEGV
from Event import Exit, Signal

class Stats:
  def __init__(self):
    self.count = dict()
    self.keys = set()

  def __IncCount(self, input, offset, byte):

    self.keys.add((input, offset))

    try:
      self.count[(input, offset, byte)]+=1
    except KeyError:
      self.count[(input, offset, byte)]=1

  def AddData(self, delta, events):

    if "Signal SIGSEGV" in map(str, events):
      self.__IncCount(delta[0], delta[1], delta[2])


  def Compute(self):

    r = []

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
            r.append([input, offset, byte]) #print (input, offset, byte), "is relevant with prob", str(prob), "!"

    return r
    #print self.keys

