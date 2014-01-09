from sklearn.feature_extraction import DictVectorizer
from src.Spec    import specs

vec = DictVectorizer(sparse = False)

def vectorizer(events):
  x = dict(map(lambda z: (z,'unit'), events))
  return vec.fit_transform([all_events,x])[1]  

#print hv
