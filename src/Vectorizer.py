from numpy import zeros, savetxt
from src.Event    import Call, Crash, Abort, specs
from src.Types    import ptypes, isPtr, isNum, ptr32_ptypes, num32_ptypes, generic_ptypes

features = []
vec_size = 0
for name,args in specs.items():
  features.append(name+":ret_addr") # return address
  features.append(name+":ret_val") # return value
  for (index, arg) in enumerate(args):
    features.append(name+"_"+str(index))

    #if isNum(arg):
    #  vec_size = vec_size + len(num32_ptypes)
    #elif isPtr(arg):
    #  vec_size = vec_size + len(ptr32_ptypes)

    #+ len(generic_ptypes)

features.append("crashed:eip")  # crash eip
features.append("crashed:addr") # crash addr

n_features = len(features)

categories = []
for ptype in ptypes:
  categories.append(str(ptype))

n_categories = len(categories)

class Vectorizer:
  def __init__(self, filename):
    self.tests = set()
    self.filename = filename
    #self.writer = csv.writer(csvfile, delimiter='\t')

  def encode(self, xs):
    r = zeros((n_features,n_categories))
    for x,y in xs:
      #try:
      print x,"=",y,"\t",
      i = features.index(x)
      j = categories.index(y)
      #except ValueError:
      #  print x,y
      #  assert(0)
      r[i,j] = 1.0

    print ""

    return r

  def preprocess(self, event):

    r = set()
    if isinstance(event, Call):
      #print event.name, event.param_types, event.ret, event.retaddr, event.retvalue
      (name, args) = event.GetTypedName()

      r.add((name+":ret_addr",str(args[0])))
      r.add((name+":ret_val",str(args[1])))

      for (index, arg) in enumerate(args[2:]):
        r.add((name+"_"+str(index),str(arg)))
        #print r
    #elif isinstance(event, Abort):
    #  pass
    elif isinstance(event, Crash):
      (name, fields) = event.GetTypedName()
      r.add((name+":eip",str(fields[0])))
      r.add((name+":addr",str(fields[1])))

    return r


  def vectorize(self,events):

    r = set()

    for event in events:
      r.update(self.preprocess(event))

    events = list(r)
    events.sort()
    #for event in events:
    #  print event

    x = hash(tuple(events))
    if (x in self.tests):
      return

    self.tests.add(x)
    #print n_categories*n_features

    v = self.encode(events)
    v.shape = (1,n_categories*n_features)

    savetxt(self.filename, v, delimiter="\t", fmt='%.1f')

    #v.shape = n_features*n_categories,

    #print r
    #assert(0)
    #events.sort()
    #return map(lambda (x,y): x+"="+y,events)

    #x = dict(map(lambda z: (z,'unit'), events))
    #return vec.fit_transform([all_events,x])[1]

#print hv
