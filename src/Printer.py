import sys
import csv
from numpy import zeros, savetxt

from src.Event    import Call, Crash, Abort, Signal, specs
from src.Types    import ptypes, isPtr, isNum, ptr32_ptypes, num32_ptypes, generic_ptypes


class Printer:
  def __init__(self, filename, pname):
    self.tests = set()
    self.file = open(filename, "a")
    self.pname = pname
    self.writer = csv.writer(self.file, delimiter='\t')

  def preprocess(self, event):

    r = set()
    if isinstance(event, Call):
      #print event.name, event.param_types, event.ret, event.retaddr, event.retvalue
      (name, args) = event.GetTypedName()

      r.add((name+":ret_addr",str(args[0])))
      r.add((name+":ret_val",str(args[1])))

      for (index, arg) in enumerate(args[2:]):
        r.add((name+":"+str(index),str(arg)))
        #print r
    elif isinstance(event, Abort):
      (name, fields) = event.GetTypedName()
      r.add((name+":eip",str(fields[0])))

    elif isinstance(event, Crash):
      (name, fields) = event.GetTypedName()
      r.add((name+":eip",str(fields[0])))

    elif isinstance(event, Signal):
      #assert(0)
      (name, fields) = event.GetTypedName()

      if name == "SIGSEGV":
        #print fields[0]
        r.add((name+":addr",str(fields[0])))
      else:
        r.add((name,str(fields[0])))

    return r


  def print_events(self,events):

    r = list()

    for event in events:
      r = r + list(self.preprocess(event))
    
    events = r

    x = hash(tuple(events))
    if (x in self.tests):
      return

    self.tests.add(x)
    
    for x,y in events:
      #x,y = event
      print str(x)+"="+str(y)+" ",
      #assert(not ("abort" in str(x)))  

    print "\n",
    return

