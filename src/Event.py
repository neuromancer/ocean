from ptrace.ctypes_tools import bytes2word
from Spec                import specs
from Types import Type, GetPtype
from Analysis import FindModule, RefinePType
from Backtrace import getBacktrace, Backtrace

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

  def __str__(self):
    return str(self.name)
    
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
    ip = process.getInstrPointer()

    self.bt =  process.getBacktrace(max_args=0, max_depth=20)
    self.module = FindModule(ip,mm)
    #print self.bt, type(self.bt)
    frames = []

    for i,frame in enumerate(self.bt.frames):
      r_type = RefinePType(Type("Ptr32",4), frame.ip, process, mm)
      frames.append(r_type)

      if str(r_type[0]) == "DPtr32":
        break
 
    self.bt.frames = frames
    #print "frames",frames
    #print "self.bt.frames", self.bt.frames
 
    self.eip = RefinePType(Type("Ptr32",4), ip, process, mm)

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("abort", [self.eip[0]])

class Timeout(Event):
  def __init__(self, secs):
    self.secs = secs
    self.name = "Timeout "+str(secs)+" secs"

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("timeouted", ["()"])

class Crash(Event):

  #relevant_regs_32 = ["eax","ebx","ecx","edx", "esp", "ebp", "esi", "edi"]

  def __init__(self, process, mm):
    ip = process.getInstrPointer()
    fp = process.getFramePointer()

    self.module = FindModule(ip,mm)
    
    self.fp_type = RefinePType(Type("Ptr32",4), fp, process, mm)
 
    #print "fp:",hex(fp_type[1]), str(fp_type[0])
    if not process.no_frame_pointer: #str(self.fp_type[0]) == "SPtr32": 
      self.bt =  getBacktrace(process,max_args=0, max_depth=20)
    else: 
      self.bt = Backtrace()
    frames = []

    for i,frame in enumerate(self.bt.frames):
      r_type = RefinePType(Type("Ptr32",4), frame.ip, process, mm)
      frames.append(r_type)
      #print "ip:", str(r_type[0])
      if not (str(r_type[0])  == "GxPtr32"):
        break

      #if str(r_type[0]) == "DPtr32":
      #  break
     
     
    self.bt.frames = frames
    self.eip_type = RefinePType(Type("Ptr32",4), process.getInstrPointer(), process, mm)

  def __str__(self):
    return "Crash@"+hex(self.eip_type[1])+":"+str(self.eip_type[0])

  def GetTypedName(self):
    return ("crashed", [self.eip_type[0]])


class Vulnerability(Event):
  def __init__(self, vtype):
    self.type = str(vtype)
    self.name = "Vulnerability "+str(vtype)+" detected"

  def __str__(self):
    return str(self.name)

  def GetTypedName(self):
    return ("Vulnerability",[str(self.type)])

def hash_events(events):
  return hash(tuple(map(str, events)))

def IsTimeout(event):
  return isinstance(event, Timeout)

