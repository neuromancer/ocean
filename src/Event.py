from ptrace.ctypes_tools import bytes2word
from Spec                import specs
from Types import Type, GetPtype
from Analysis import RefinePType

#from distorm import Decode, Decode32Bits

class Event:
  def __init__(self):
    pass

class Call(Event):

  def __init__(self, name):

    assert(name in specs)
    spec = specs[name]
    self.ret = str(spec[0])
    #fixme: void functions and non-returned values should be different!
    self.retvalue = (Type("Top32",4),None)
    self.name = str(name)
    self.param_types = list(spec[1:])
    self.param_ptypes = []
    self.param_values = []
    self.dim = 256
    self.v = None

  def __str__(self):
    return "call"
    pass
    """
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
    """

  def __DetectRetAddr__(self):
    addr = self.process.getreg("esp")
    bytes = self.process.readBytes(addr, 4)
    return RefinePType(Type("Ptr32",4),bytes2word(bytes), self.process, self.mm)
    #return bytes2word(bytes)

  def __DetectParam__(self, ptype, offset):
    addr = self.process.getreg("esp")+offset
    bytes = self.process.readBytes(addr, 4)
    return RefinePType(GetPtype(ptype),bytes2word(bytes), self.process, self.mm)


  def GetReturnAddr(self):
    return self.retaddr[1]

  def DetectParams(self, process, mm):
    self.process = process
    self.mm      = mm
    self.retaddr = self.__DetectRetAddr__()

    offset = 4
    #print self.mm
    #print self.name
    for ctype in self.param_types:
      #print ctype

      (ptype, value) = self.__DetectParam__(ctype, offset)
      self.param_values.append(value)
      self.param_ptypes.append(ptype)
      offset += ptype.getSize()

  def DetectReturnValue(self, process):
    self.process = process
    self.retvalue = RefinePType(GetPtype(self.ret),process.getreg("eax"), self.process, self.mm)


  def GetTypedName(self):

    return (str(self.name), [self.retaddr[0],self.retvalue[0]]+list(self.param_ptypes))

class Signal(Event):
  def __init__(self, name, process, mm): #_sifields = None):

    self.fields = dict()
    _sifields = process.getsiginfo()._sifields

    self.name = name

    if hasattr(_sifields, "_sigfault") and self.name == "SIGSEGV":
      self.fields["addr"] = RefinePType(Type("Ptr32",4), _sifields._sigfault._addr, process, mm)



  def __str__(self):
    return str(self.name)

  def GetTypedName(self):

    if len(self.fields) > 0:
      ptypes = map(lambda (x,_): x, self.fields.values())
      return (str(self.name), ptypes)
    else:
      return (str(self.name), ["()"])


class Syscall(Event):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Syscall", [str(self.name)])

class Exit(Event):
  def __init__(self, code):
    self.code = code
    self.name = "Exit with "+str(code)

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("exited", str(self.code))

class Abort(Event):
  def __init__(self, process, mm):
    self.name = "Abort"
    self.eip = RefinePType(Type("Ptr32",4), process.getInstrPointer(), process, mm)

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("abort", [self.eip[0]])#

class Timeout(Event):
  def __init__(self, secs):
    self.code = secs
    self.name = "Timeout "+str(secs)+" secs"

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Timeout", "unit")

class Crash(Event):

  #relevant_regs_32 = ["eax","ebx","ecx","edx", "esp", "ebp", "esi", "edi"]

  def __init__(self, process, mm):
    #self.raw_regs = process.getregs()
    #self.regs = dict()
    #for name, type in self.raw_regs._fields_:

    #  if name in self.relevant_regs_32:
    #    value = getattr(self.raw_regs, name)
    #    self.regs[name] = hex(value).replace("L","")

    #print hex(process.getInstrPointer())
    self.eip = RefinePType(Type("Ptr32",4), process.getInstrPointer(), process, mm)


    #ins = Decode(self.eip, process.readBytes(self.eip, 8), Decode32Bits)[0]
    #self.address, self.size, self.text, self.hexa = ins
    #print ins.operands

    #print process.disassembleOne()

  def __str__(self):
    #if self.faulty_addr is None:
    return "Crash@"+hex(self.eip)
    #else:
    #  return "Crash@"+hex(self.eip)+" -> "+hex(self.faulty_addr).replace("L", "")

  def GetTypedName(self):
    return ("crashed", [self.eip[0]])#, self.faulty_addr[0]])

def hash_events(events):
  return hash(tuple(map(str, events)))

# functions
#all_events = dict(map(lambda x,y: (x,len(y)), specs.items()))

# termination
#all_events[str(Crash())] = 'unit'
#all_events[str(Abort())] = 'unit'




