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
    self.filters = []
    self.writer = csv.writer(self.file, delimiter='\t')

  def preprocess(self, event):

    r = set()
    if isinstance(event, Call):
      #print event.name, event.param_types, event.ret, event.retaddr, event.retvalue
      (name, args) = event.GetTypedName()

      #r.add((name+":ret_addr",str(args[0])))
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

  def filter_by(self, filter_str):
    
    if '=' in filter_str:
      self.filters.append(tuple(filter_str.split('=')))
    else:
      print "Invalid fiter:", filter_str
  
  def split_events(self, events):
    r = dict()
    
    for event in events:
      if isinstance(event, Call): #or isinstance(event, Crash):
        mod = event.module
        #else:
        #  mod = self.pname
        #print mod 
        if mod is not None:
          if mod in r:
            r[mod] = r[mod] + [event]
          else:
            r[mod] = [event]
      

    return r

  def merge_events(self, events):
     r = dict()
     r[self.pname] = events
     return r
  
  def print_events(self, events, mode):
    if mode == "split": 
      r = self.split_events(events)
    elif mode == "merge":
      r = self.merge_events(events)
    
    for mod,evs in r.items():
      #print mod, evs
      self.__print_events(mod,evs)
     
  def __print_events(self,module,events):
   
    r = list()

    for event in events:
      r = r + list(self.preprocess(event))
    
    events = r

    if not (self.filters == [] or any(map(lambda f: f in events,self.filters))):
      return

    x = hash(tuple(events))
    if (x in self.tests):
      return

    self.tests.add(x)
    print module+"\t", 
    for x,y in events:
      #x,y = event
      print x+"="+y+" ",
      #assert(not ("abort" in str(x)))  

    print "\n",
    return

