from sklearn.feature_extraction import DictVectorizer
from src.Event    import all_events

vec = DictVectorizer(sparse = False)

def vectorizer(events):
  events = list(set(map(lambda x: x.GetTypedName(), events)))
  events.sort()
  return map(lambda (x,y): x+"="+y,events)

  #x = dict(map(lambda z: (z,'unit'), events))
  #return vec.fit_transform([all_events,x])[1]

#print hv
