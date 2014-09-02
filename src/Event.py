from ptrace.ctypes_tools import bytes2word
from Spec                import specs
from Types import Type, GetPtype
from Analysis import FindModule, RefinePType

#from distorm import Decode, Decode32Bits

class Event:
  module = None
  def __init__(self):
    pass

class Call(Event):

  def __init__(self, name, module):

    assert(name in specs)
    spec = specs[name]
    self.ret = str(spec[0])
    #fixme: void functions and non-returned values should be different!
    self.retvalue = (Type("Top32",4),None)
    self.module = module
    self.name = str(name)
    self.param_types = list(spec[1:])
    self.param_ptypes = []
    self.param_values = []
    #self.dim = 256
    #self.v = None

  def __str__(self):
    return "call"
    
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
    self.retaddr = None #self.__DetectRetAddr__()
    #print  "ret_addr:", str(self.retaddr[0]), hex(self.retaddr[1])

    offset = 4
    #print self.mm
    #print self.name
    for ctype in self.param_types:

      (ptype, value) = self.__DetectParam__(ctype, offset)
      self.param_values.append(value)
      self.param_ptypes.append(ptype)
      offset += ptype.getSize()

  def DetectReturnValue(self, process):
    self.process = process
    self.retvalue = RefinePType(GetPtype(self.ret),process.getreg("eax"), self.process, self.mm)

  def GetTypedName(self):
    return (str(self.name), list(self.param_ptypes))

class Signal(Event):
  def __init__(self, name, process, mm): #_sifields = None):

    self.fields = dict()
    _sifields = process.getsiginfo()._sifields

    self.name = name

    if hasattr(_sifields, "_sigfault") and self.name == "SIGSEGV":
      self.fields["addr"] = RefinePType(Type("Ptr32",4), _sifields._sigfault._addr, process, mm)
      #print "sigfault @",  _sifields._sigfault._addr



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

    self.bt =  process.getBacktrace(max_args=0, max_depth=20)
    frames = self.bt.frames

    for i,frame in enumerate(frames):
      r_type = RefinePType(Type("Ptr32",4), frame.ip, process, mm)
      frames[i] = r_type
      if str(r_type[0]) == "DPtr32":
        frames = frames[:i+1]
        break

    self.eip = RefinePType(Type("Ptr32",4), process.getInstrPointer(), process, mm)

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("abort", [self.eip[0]])

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

    #print "crash @",hex(process.getInstrPointer())
    self.module = FindModule(process.getInstrPointer(),mm)

    self.bt =  process.getBacktrace(max_args=0, max_depth=20)
    frames = self.bt.frames
    for i,frame in enumerate(frames):
      r_type = RefinePType(Type("Ptr32",4), frame.ip, process, mm)
      frames[i] = r_type
      #print hex(r_type[1])
      if str(r_type[0]) == "DPtr32":
        frames = frames[:i+1]
        break

    self.eip = RefinePType(Type("Ptr32",4), process.getInstrPointer(), process, mm)

    #ins = Decode(self.eip, process.readBytes(self.eip, 8), Decode32Bits)[0]
    #self.address, self.size, self.text, self.hexa = ins
    #print ins.operands

    #print process.disassembleOne()

  def __str__(self):
    return "Crash@"+hex(self.eip[1])+":"+str(self.eip[0])

  def GetTypedName(self):
    #if self.smashed_stack:
    #  return ("vulnerable_crash", [self.eip[0]])
    #else: 
    return ("crashed", [self.eip[0]])


class Vulnerability(Event):
  def __init__(self, vtype):
    self.type = vtype
    self.name = "Vulnerability "+str(vtype)+" detected"

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Vulnerability",[str(self.type)])

def hash_events(events):
  return hash(tuple(map(str, events)))

# functions
#all_events = dict(map(lambda x,y: (x,len(y)), specs.items()))

# termination
#all_events[str(Crash())] = 'unit'
#all_events[str(Abort())] = 'unit'




