import sys
import csv
from numpy import zeros, savetxt

from src.Event    import Call, Crash, Abort, Signal, specs
from src.Types    import ptypes, isPtr, isNum, ptr32_ptypes, num32_ptypes, generic_ptypes

"""
features = dict()
vec_size = 0
unit = ["()"]

for name,args in specs.items():
  features[name+":ret_addr"] = (vec_size, ptr32_ptypes+generic_ptypes) # return address
  vec_size = vec_size + len(ptr32_ptypes+generic_ptypes)
  features[name+":ret_val"] = (vec_size, ptypes)                       # return value
  vec_size = vec_size + len(ptypes)

  for (index, arg) in enumerate(args[1:]):
    #features.append(name+"_"+str(index))
    #print name+"_"+str(index), arg

    if isNum(arg):
      features[name+"_"+str(index)] = (vec_size, num32_ptypes+generic_ptypes)
      vec_size = vec_size + len(num32_ptypes+generic_ptypes)
    elif isPtr(arg):
      features[name+"_"+str(index)] = (vec_size, ptr32_ptypes+generic_ptypes)
      vec_size = vec_size + len(ptr32_ptypes+generic_ptypes)
    else:
      features[name+"_"+str(index)] = (vec_size, generic_ptypes)
      vec_size = vec_size + len(generic_ptypes)

    #+ len(generic_ptypes)

features["crashed:eip"] = (vec_size, ptr32_ptypes+generic_ptypes)  # crash eip
vec_size = vec_size + len(ptr32_ptypes+generic_ptypes)

features["abort:eip"] = (vec_size, ptr32_ptypes+generic_ptypes) # abort eip
vec_size = vec_size + len(ptr32_ptypes+generic_ptypes)

features["SIGSEGV:addr"] = (vec_size, ptr32_ptypes+generic_ptypes) # sigsegv faulty addr
vec_size = vec_size + len(ptr32_ptypes+generic_ptypes)

features["SIGABRT"] = (vec_size, unit) # sigsegv faulty addr
vec_size = vec_size + len(unit)

features["SIGFPE"] = (vec_size, unit) # sigsegv faulty addr
vec_size = vec_size + len(unit)

features["SIGBUS"] = (vec_size, unit) # sigsegv faulty addr
vec_size = vec_size + len(unit)

features["SIGCHLD"] = (vec_size, unit) # sigsegv faulty addr
vec_size = vec_size + len(unit)

n_features = vec_size
"""
  
#for pt in ptypes:
#    print str(pt)

#print vec_size
#assert(0)

#labels = sorted(features.items(), key=lambda (x,(i,y)): i)
#for  f,(_,ts) in labels:
#  for pt in ts:
#    print str(f)+"="+str(pt)+"\t",
#assert(0)

#for f,(i,_) in features.items():
#    print x,"=",y,"\t",

#print n_features
#assert(0)


# features = []
# vec_size = 0
# for name,args in specs.items():
#   features.append(name+":ret_addr") # return address
#   features.append(name+":ret_val") # return value
#   for (index, arg) in enumerate(args):
#     features.append(name+"_"+str(index))
#
#     #if isNum(arg):
#     #  vec_size = vec_size + len(num32_ptypes)
#     #elif isPtr(arg):
#     #  vec_size = vec_size + len(ptr32_ptypes)
#
#     #+ len(generic_ptypes)
#
# features.append("crashed:eip")  # crash eip
# features.append("abort:eip")  # abort eip
# features.append("SIGSEGV:addr") # sigsegv faulty addr
#
# n_features = len(features)

# categories = []
# for ptype in ptypes:
#   categories.append(str(ptype))
#
# n_categories = len(categories)

class Printer:
  def __init__(self, filename, pname):
    self.tests = set()
    self.file = open(filename, "a")
    self.pname = pname
    self.writer = csv.writer(self.file, delimiter='\t')

  #def write_header(self):

  #  labels = sorted(features.items(), key=lambda (x,(i,y)): i)
  #  for  f,(_,ts) in labels:
  #    for pt in ts:
  #      print str(f)+"="+str(pt)+"\t",
  #  #self.writer.writerow(map(lambda f,(i,_): f+"="+str(i), features.items()))
  #  #for f,(i,_) in features.items():
  #  #print x,"=",y,"\t",
  """
  def encode(self, xs):
    r = zeros(n_features)
    #print self.pname, "\t",
    for x,y in xs:
      try:
        #print x,"=",y,"\t",
        i,categories = features[x]
        categories = map(str, list(categories))
        #print categories
        j = categories.index(y)
        r[i+j] = 1.0
      except ValueError:
        print "Error:",x,y

        assert(0)

    #print "\n-----"

    return r
  """

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

    #r = set()
    r = list()

    for event in events:
      #print event
      r = r + list(self.preprocess(event))

    #events = list(r)
    #events.sort()
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


    #if self.raw:
    #  for x,y in events:
    #    print str(x)+"="+str(y)+"\t",

    #  print "\n",
    #  return
    #print n_categories*n_features
    """

    v = self.encode(events)
    v.shape = (1,n_features)

    print self.pname+"\t",
    savetxt(sys.stdout, v, delimiter="\t", fmt='%.1f')
    """
    #v.shape = n_features*n_categories,

    #print r
    #assert(0)
    #events.sort()
    #return map(lambda (x,y): x+"="+y,events)

    #x = dict(map(lambda z: (z,'unit'), events))
    #return vec.fit_transform([all_events,x])[1]

#print hv
