import ast

from ptrace.ctypes_tools import bytes2word

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

from scipy.sparse import hstack
from scipy.linalg import norm


f = open("/etc/ltrace.conf")
specs = dict()

for raw_spec in f.readlines():
    raw_spec = raw_spec.replace("\n", "")
    raw_spec = raw_spec.replace(", ", ",")
    raw_spec = raw_spec.replace(" (", "(")
    raw_spec = raw_spec.replace("  ", " ")
    raw_spec = raw_spec.replace("  ", " ")
    if raw_spec <> "" and raw_spec[0] <> ";":
        x = raw_spec.split(" ")
        ret = x[0]
        x = x[1].split("(")
        name = x[0]
        param_types  = x[1].replace(");", "").split(",")
        specs[name] = [ret] + param_types

#print specs

class Event:
  def __init__(self):
    pass

class Call(Event):

  def __init__(self, name):

    assert(name in specs)
    spec = specs[name]
    self.ret = str(spec[0])
    self.name = str(name)
    self.param_types = list(spec[1:])
    self.param_values = []
    self.dim = 256
    self.v = None

    self.hasher = HashingVectorizer(encoding='iso-8859-15', n_features=self.dim / 2,
                                    analyzer='char', tokenizer=lambda x: [x],
                                    ngram_range=(1, 3), lowercase=False)

  def __str__(self):
    if self.param_values == []:
      #return str(self.ret + " " + self.name + "(" + ",".join(self.param_types) + ")")
      return str(self.name)
    else:
      return str([self.ret, self.name] +self.param_values)

  def __GetSize__(self, ptype):
    if   ptype == "int":
      return 4
    elif ptype == "unit":
      return 4
    elif ptype == "ulong":
      return 4
    elif ptype == "string":
      return 4

  def __DetectParam__(self, ptype, offset):
   if ptype == "string":

     addr = self.process.getreg("esp")+offset
     bytes = self.process.readBytes(addr, 4)
     #print bytes
     return self.process.readCString(bytes2word(bytes), 512)[0]

   elif (ptype == "ulong"):
     addr = self.process.getreg("esp")+offset
     bytes = self.process.readBytes(addr, 4)
     return bytes2word(bytes)
   else:
     return ""

  def DetectParams(self, process):
    self.process = process

    offset = 4
    for ptype in self.param_types:

      x = self.__DetectParam__(ptype, offset)
      self.param_values.append(x)
      offset += self.__GetSize__(ptype)

  def GetVector(self):
    if self.v is None:
      vs = self.hasher.transform(self.param_values[0:2])
      self.v = normalize(hstack(list(vs)), norm='l1', axis=1)

    return self.v

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

  def DetectParams(self, process):
    Call.DetectParams(self, process)

    slen = self.param_values[2]
    for i in range(2):
      if len(self.param_values[i]) > slen:
        self.param_values[i] = self.param_values[i][0:slen]


#etable = [("strncmp@plt",StrncmpCall)]

#def GetEvent(raw):
#  rlist = ast.literal_eval(raw)
#  for (e, c) in etable:
#    if e == rlist[1]:
#      return c(rlist)
#
#  return None

# End event

class Exit(Event):
  def __init__(self, code):
    self.code = code
    self.name = "Exit with "+str(code)

  def __str__(self):
    return str(self.name)

class Timeout(Event):
  def __init__(self, secs):
    self.code = secs
    self.name = "Timeout "+str(secs)+" secs"

  def __str__(self):
    return str(self.name)

class Crash(Event):
  def __init__(self, process):
    self.regs = process.getregs()
    #for name, type in regs._fields_:
    #  value = getattr(regs, name)
    #  print name, "->", hex(value),
    self.eip = process.getInstrPointer()

  def __str__(self):
    return "Crash@"+hex(self.eip)


