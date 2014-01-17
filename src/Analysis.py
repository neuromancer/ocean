from Types import Type
from ptrace.error import PtraceError

def RefinePType(ptype, value, process, mm):

  if value is None:
    return (Type("Top32",4), value)

  if str(ptype) == "Ptr32":
    ptr = value
    if ptr == 0x0:
      return (Type("NPtr32",4), ptr)
    else:

      try:
          _ = process.readBytes(ptr, 1)
      except PtraceError:
        #print "Dptr", hex(ptr)
        return (Type("DPtr32",4), ptr)

      mm.checkPtr(ptr)
      if   mm.isStackPtr(ptr):
        return (Type("SPtr32",4), ptr)
      elif mm.isHeapPtr(ptr):
        return (Type("HPtr32",4), ptr)
      elif mm.isLibPtr(ptr):
        return (Type("LPtr32",4), ptr)
      elif mm.isFilePtr(ptr):
        return (Type("FPtr32",4), ptr)
      elif mm.isGlobalPtr(ptr):
        return (Type("GPtr32",4), ptr)
      else:
        return (Type("Ptr32",4), ptr)

  elif str(ptype) == "Num32":
    num = value
    if num == 0x0:
      return (Type("Num32B0",4), num)
    else:
      binlen = len(bin(num))-2
      return (Type("Num32B"+str(binlen),4), num)

  return (Type("Top32",4), value)
