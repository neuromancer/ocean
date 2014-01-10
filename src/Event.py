from ptrace.ctypes_tools import bytes2word
from Spec                import specs
#from sklearn.feature_extraction.text import HashingVectorizer
#from sklearn.preprocessing import normalize

#from scipy.sparse import hstack
#from scipy.linalg import norm

#from distorm import Decode, Decode32Bits

def isNum(ptype):
  return ptype in ["int", "ulong", "long"]

def isPtr(ptype):
  return "addr" in ptype or "*" in ptype or "string" in ptype or "format" in ptype or "file" in ptype

def isVoid(ptype):
  return ptype == "void"

def isNull(val):
  return val == "0x0" or val == "0"

def GetPTypeSize(ptype):
  return 4

  #if   ptype == "int":
  #  return 4
  #elif ptype == "ulong":
  #  return 4
  #elif ptype == "addr":
  #  return 4
  #elif "string" in ptype:
  #  return 4

  #print ptype
  #return 4

def GetPtypeStr((ptype, value)):

  if value is None:
    return "_"

  if isPtr(ptype):
    return hex(value).replace("L","")
  elif isNum(ptype):
    return str(value)
  elif isVoid(ptype):
    return ""
  else:
    return "_"

class Event:
  def __init__(self):
    pass

class Call(Event):

  def __init__(self, name):

    assert(name in specs)
    spec = specs[name]
    self.ret = str(spec[0])
    self.retvalue = None
    self.name = str(name)
    self.param_types = list(spec[1:])
    self.param_values = []
    self.dim = 256
    self.v = None

    #self.hasher = HashingVectorizer(encoding='iso-8859-15', n_features=self.dim / 2,
    #                                analyzer='char', tokenizer=lambda x: [x],
    #                                ngram_range=(1, 3), lowercase=False)

  def __str__(self):
    if self.param_values == []:
      #return str(self.ret + " " + self.name + "(" + ",".join(self.param_types) + ")")
      return str(self.name)
    else:
      params   = map(GetPtypeStr, zip(self.param_types,self.param_values))

      if self.retvalue is None:
        retvalue = ".."
      else:
        retvalue = GetPtypeStr((self.ret, self.retvalue))

      retaddr  = GetPtypeStr(("addr", self.retaddr))

      return retaddr + ": " + self.name + "(" + ", ".join(params) + ")" + " = " + retvalue
      #return str([self.ret, self.name] +self.param_values)

  def __DetectRetAddr__(self):
    addr = self.process.getreg("esp")
    bytes = self.process.readBytes(addr, 4)
    return bytes2word(bytes)

  def __DetectParam__(self, ptype, offset):

   if isPtr(ptype):

     addr = self.process.getreg("esp")+offset
     bytes = self.process.readBytes(addr, 4)
     return bytes2word(bytes)

   elif isNum(ptype):
     addr = self.process.getreg("esp")+offset
     bytes = self.process.readBytes(addr, 4)
     return bytes2word(bytes)
   else:
     return None

  def GetParameters(self):
    params = map(GetPtypeStr, zip(self.param_types,self.param_values))
    return zip(self.param_types, params)

  def GetReturnValue(self):
    #print "ret:",self.ret
    ret = map(GetPtypeStr, zip([self.ret],[self.retvalue]))
    return zip([self.ret], ret)

  def GetReturnAddr(self):
    return self.retaddr

  def DetectParams(self, process):
    self.process = process
    self.retaddr = self.__DetectRetAddr__()

    offset = 4
    for ptype in self.param_types:

      x = self.__DetectParam__(ptype, offset)
      self.param_values.append(x)
      offset += GetPTypeSize(ptype)

  def DetectReturnValue(self, process):
    self.retvalue = process.getreg("eax")

  def GetTypedName(self):

    params = self.GetParameters()
    params_str = ""

    for i in range(len(params)):
      type, value = params[i]
      if isPtr(type):
        if isNull(value):
          params_str = params_str + "NULLPTR,"
        else:
          params_str = params_str + "PTR,"
      elif isNum(type):
          value = int(value)
          binlen = len(bin(value))-1
          params_str = params_str + "BIN_"+ str(binlen) + ","

    return (str(self.name), params_str)

  #def GetVector(self):
  #  if self.v is None:
  #    vs = self.hasher.transform(self.param_values[0:2])
  #    self.v = normalize(hstack(list(vs)), norm='l1', axis=1)
  #
  #  return self.v

import pydot

class Signal(Event):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Signal", str(self.name))


class Syscall(Event):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Syscall", str(self.name))



#class StrncmpCall(Call):
#  def __init__(self, raw):
#    Call.__init__(self, raw)
#
#  def DetectParams(self, process):
#    Call.DetectParams(self, process)
#
#    slen = self.param_values[2]
#    for i in range(2):
#      if len(self.param_values[i]) > slen:
#        self.param_values[i] = self.param_values[i][0:slen]


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

  def GetTypedName(self):
    return ("Exit", str(self.code))

class Abort(Event):
  def __init__(self):
    self.name = "Abort"

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Abort", "unit")

class Timeout(Event):
  def __init__(self, secs):
    self.code = secs
    self.name = "Timeout "+str(secs)+" secs"

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Timeout", "unit")

class Crash(Event):

  relevant_regs_32 = ["eax","ebx","ecx","edx", "esp", "ebp", "esi", "edi"]

  def __init__(self, process, faulty_addr = None):
    self.raw_regs = process.getregs()
    self.regs = dict()
    for name, type in self.raw_regs._fields_:

      if name in self.relevant_regs_32:
        value = getattr(self.raw_regs, name)
        self.regs[name] = hex(value).replace("L","")

    self.eip = process.getInstrPointer()
    self.faulty_addr = faulty_addr
    #ins = Decode(self.eip, process.readBytes(self.eip, 8), Decode32Bits)[0]
    #self.address, self.size, self.text, self.hexa = ins
    #print ins.operands

    #print process.disassembleOne()

  def __str__(self):

    if self.faulty_addr is None:
      return "Crash@"+hex(self.eip)
    else:
      return "Crash@"+hex(self.eip)+" -> "+hex(self.faulty_addr).replace("L", "")

  def GetTypedName(self):
    return ("Crash", hex(self.eip))

def hash_events(events):
  return hash(tuple(map(str, events)))



# functions
all_events = dict(map(lambda x: (x,'unit'), specs))

# termination
#all_events[str(Crash())] = 'unit'
#all_events[str(Abort())] = 'unit'




