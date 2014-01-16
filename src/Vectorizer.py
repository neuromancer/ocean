from numpy import zeros, savetxt
from src.Event    import Call, specs
from src.Types    import ptypes


features = []
for name,args in specs.items():
  for (index, arg) in enumerate(args):
    features.append(name+"_"+str(index))

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
      i = features.index(x)
      j = categories.index(y)
      #except ValueError:
      #  print x,y
      #  assert(0)
      r[i,j] = 1.0

    return r

  def preprocess(self, event):

    r = set()
    if isinstance(event, Call):
      (name, args) = event.GetTypedName()

      for (index, arg) in enumerate(args):
        r.add((name+"_"+str(index),str(arg)))
        #print r

    return r


  def vectorize(self,events):

    r = set()

    for event in events:
      r.update(self.preprocess(event))

    events = list(r)
    events.sort()

    x = hash(tuple(events))
    if (x in self.tests):
      return

    self.tests.add(x)
    print n_categories*n_features

    v = self.encode(events)
    v.shape = (1,n_categories*n_features)

    savetxt(self.filename, v, delimiter=",")

    #v.shape = n_features*n_categories,

    #print r
    #assert(0)
    #events.sort()
    #return map(lambda (x,y): x+"="+y,events)

    #x = dict(map(lambda z: (z,'unit'), events))
    #return vec.fit_transform([all_events,x])[1]

#print hv
