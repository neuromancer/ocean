import ast
from sklearn.feature_extraction.text import HashingVectorizer
from scipy.sparse import hstack

class Event:
  def __init__(self):
    pass

class Call(Event):

  def __init__(self, rlist):

    self.ret = rlist[0]
    self.name = rlist[1]
    self.param_values = rlist[2:]
    self.hasher = HashingVectorizer(encoding='iso-8859-15', n_features=512,
                                    analyzer='char', tokenizer=lambda x: [x],
                                    ngram_range=(1, 3), lowercase=False)

  def __str__(self):
    return repr([self.ret, self.name] + self.param_values)

  def GetVector(self):
    vs = self.hasher.transform(self.param_values[0:2])
    return hstack(list(vs))

class Signal(Event):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)


class Syscall(Event):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)


class StrncmpCall(Call):
  def __init__(self, raw):
    Call.__init__(self, raw)

    slen = self.param_values[2]
    for i in range(2):
      if len(self.param_values[i]) > slen:
        self.param_values[i] = self.param_values[i][0:slen]


etable = [("strncmp@plt",StrncmpCall)]

def GetEvent(raw):
  rlist = ast.literal_eval(raw)
  for (e, c) in etable:
    if e == rlist[1]:
      return c(rlist)

  return None





