import sys
import csv
import copy

from src.Event    import Call, Crash, Abort, Exit, Timeout, Signal, Vulnerability, specs
from src.Types    import ptypes, isPtr, isNum, ptr32_ptypes, num32_ptypes, generic_ptypes

class TypePrinter:
  def __init__(self, filename, pname):
    self.tests = set()
    self.file = open(filename, "a")
    self.pname = pname
    self.writer = csv.writer(self.file, delimiter='\t')

  def preprocess(self, event):

    r = list()

    if isinstance(event, Call):
      (name, args) = event.GetTypedName()

      for (index, arg) in enumerate(args[:]):
        r.append((name+":"+str(index),str(arg)))
    
    elif isinstance(event, Abort):
      (name, fields) = event.GetTypedName()
      r.append((name+":eip",str(fields[0])))
    
    elif isinstance(event, Exit):
      (name, fields) = event.GetTypedName()
      r.append((name,str(())))
    
    elif isinstance(event, Crash):
      (name, fields) = event.GetTypedName()
      r.append((name+":eip",str(fields[0])))

    elif isinstance(event, Vulnerability):
      (name, fields) = event.GetTypedName()
      r.append((name,str(fields[0])))

    elif isinstance(event, Timeout):
      (name, fields) = event.GetTypedName()
      r.append((name,str(())))

    elif isinstance(event, Signal):
      (name, fields) = event.GetTypedName()

      if name == "SIGSEGV":
        r.append((name+":addr",str(fields[0])))
      else:
        r.append((name,str(fields[0])))

    return r

  def print_events(self, delta, events):
     
    r = list()

    for event in events:
      r = r + list(self.preprocess(event))
    
    events = r

    x = hash(tuple(events))
   
    if (x in self.tests):
      return

    self.tests.add(x)
   
    print self.pname+"\t"+str(delta)+"\t", 
    for x,y in events:
      print x+"="+y,
    print ""

    sys.stdout.flush()
    return
