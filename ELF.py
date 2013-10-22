import re
import subprocess

_READELF = '/usr/bin/readelf'
_OBJDUMP = '/usr/bin/objdump'

def die(s):
  print s
  exit(-1)

def check(f):
  import os
  if not (os.access(f, os.X_OK) and os.path.isfile(f)):
    die('Executable %s needed for readelf.py, please install binutils' % f)

check(_READELF)
check(_OBJDUMP)

def plt_got(path):
  plt, got = dict(), dict()

  cmd = [_OBJDUMP, '-d', path]
  out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
  got32 = '[^j]*jmp\s+\*0x(\S+)'
  got64 = '[^#]*#\s+(\S+)'
  lines = re.findall('([a-fA-F0-9]+)\s+<([^@<]+)@plt>:(%s|%s)' % (got32, got64), out)

  for addr, name, _, gotaddr32, gotaddr64 in lines:
     addr = int(addr, 16)
     gotaddr = int(gotaddr32 or gotaddr64, 16)
     plt[name] = addr
     got[name] = gotaddr

  return plt, got


#def symbols(file):
#    import re, subprocess
#    symbols = {}
#    # -s : symbol table
#    cmd = [_READELF, '-s', file]
#    out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
#    field = '\s+(\S+)'
#    lines = re.findall('^\s+\d+:' + field * 7 + '$', out, re.MULTILINE)
#
#    for addr, size, type, _bind, _vis, _ndx, name in lines:
#        addr = int(addr, 16)
#        size = int(size, 10)
#        if addr <> 0 and name <> '':
#            symbols[name] = {'addr': addr,
#                             'size': size,
#                             'type': type,
#                             }
#    return symbols

class ELF:
  '''A parsed ELF file'''

  def __init__(self, path):
    self.path = str(path)
    self.plt, self.got = plt_got(self.path)
    self.name2addr = self.plt
    self.addr2name = dict()

    for (name, addr) in self.name2addr.items():
      self.addr2name[addr] = name

    self.name2func = self.got
    self.func2name = dict()

    for (name, addr) in self.name2func.items():
      self.func2name[addr] = name

  def FindFuncInPlt(self, name):

    if name in self.name2addr:
      return self.name2addr[name]
    else:
      return None

  def FindAddrInPlt(self, addr):
    #print addr
    if addr in self.addr2name:
      return self.addr2name[addr]
    else:
      return None

  def FindFuncInGot(self, name):

    if name in self.name2addr:
      return self.name2func[name]
    else:
      return None

  def FindAddrInGot(self, addr):
    #print addr
    if addr in self.addr2name:
      return self.func2name[addr]
    else:
      return None