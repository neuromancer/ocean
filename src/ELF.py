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

# def symbols(file):
#     import re, subprocess
#     symbols = {}
#     # -s : symbol table
#     cmd = [_READELF, '-s', file]
#     out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
#     field = '\s+(\S+)'
#     lines = re.findall('^\s+\d+:' + field * 7 + '$', out, re.MULTILINE)
#
#     for addr, size, type, _bind, _vis, _ndx, name in lines:
#         addr = int(addr, 16)
#         size = int(size, 10)
#         if addr <> 0 and name <> '':
#             symbols[name] = {'addr': addr,
#                              'size': size,
#                              'type': type,
#                              }
#     return symbols

def plt_got(path, base):
  plt, got = dict(), dict()

  cmd = [_OBJDUMP, '-d', path]
  out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
  got32 = '[^j]*jmp\s+\*0x(\S+)'
  got64 = '[^#]*#\s+(\S+)'
  lines = re.findall('([a-fA-F0-9]+)\s+<([^@<]+)@plt>:(%s|%s)' % (got32, got64), out)

  for addr, name, _, gotaddr32, gotaddr64 in lines:
     addr = int(addr, 16)

     try:
       gotaddr = int(gotaddr32 or gotaddr64, 16)
     except ValueError:
       gotaddr = None

     plt[name] = base + addr
     got[name] = gotaddr

  return plt, got

def entrypoint(path):
    cmd = [_READELF, '-hWS', path]
    out = subprocess.check_output(cmd)

    #elfclass = re.findall('Class:\s*(.*$)', out, re.MULTILINE)[0]
    entrypoint = int(re.findall('Entry point address:\s*(.*$)', out, re.MULTILINE)[0], 16)

    return entrypoint

class ELF:
  '''A parsed ELF file'''

  def __init__(self, path, base = 0x0):
    self.path = str(path)
    self.base = base
    self.sections = dict()

    self.entrypoint = entrypoint(path)
    self._load_sections()

    self.plt, self.got = plt_got(self.path, self.base)
    self.name2addr = self.plt
    self.addr2name = dict()

    for (name, addr) in self.name2addr.items():
      self.addr2name[addr] = name

    self.name2func = self.got
    self.func2name = dict()

    for (name, addr) in self.name2func.items():
      self.func2name[addr] = name


  def _load_sections(self):
    # -W : Wide output
    # -S : Section headers
    cmd = [_READELF, '-W', '-S', self.path]
    out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    field = '\s+(\S+)'
    posint = '[123456789]\d*'
    flags = '\s+([WAXMSILGTExOop]*)'
    lines = re.findall('^\s+\[\s*' + posint + '\]' + field * 6 + flags, out, re.MULTILINE)

    for name, _type, addr, off, size, _es, flgs in lines:
      addr = int(addr, 16)
      off = int(off, 16)
      size = int(size, 16)
      self.sections[name] = {'addr'  : addr,
                             'offset': off,
                             'size'  : size,
                             'flags' : flgs,
                             }


  def GetEntrypoint(self):
    return self.entrypoint

  def GetFunctions(self):
    return self.name2func.keys()

  def GetModname(self):
    return str(self.path)

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