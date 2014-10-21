import re
import csv
import os
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

realpath = os.path.dirname(os.path.realpath(__file__))
datadir = "../cache/"

def _save_cached_data(path, plt, got, base):
  filename = realpath+"/"+datadir+"/"+str(path.replace("/","_"))
  csvfile = open(filename+".plt", 'wb')
  writer = csv.writer(csvfile, delimiter='\t')

  for (name,addr) in plt.items():
    if addr is not None:
      writer.writerow((name,addr-base))

  csvfile = open(filename+".got", 'wb')
  writer = csv.writer(csvfile, delimiter='\t')

  for (name,addr) in got.items():
    if addr is not None:
      writer.writerow((name,addr))
  
def _load_cached_data(path, plt, got, base):
  
  filename = realpath+"/"+datadir+"/"+str(path.replace("/","_"))
  try: 
      csvfile = open(filename+".plt", 'rb')
  except IOError:
      return False
  reader = csv.reader(csvfile, delimiter='\t')
  
  for (name,addr) in reader:
      plt[name] = int(addr)+base


  try:
      csvfile = open(filename+".got", 'rb')
  except IOError:
      return False
 
  reader = csv.reader(csvfile, delimiter='\t')

  for (name,addr) in reader:
      got[name] = int(addr)

  return True

def plt_got(path, base):
  plt, got = dict(), dict()

  if _load_cached_data(path, plt, got, base):
    return plt, got

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

  _save_cached_data(path, plt, got, base)
  return plt, got

def load_plt_calls(path):
  cmd = [_OBJDUMP, '-d', '-j', ".text", path]
  raw_instructions = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
  lines = re.findall('([a-fA-F0-9]+)\s+<([^@<]+)@plt>', raw_instructions)
  return lines

def entrypoint(path):
    cmd = [_READELF, '-hWS', path]
    out = subprocess.check_output(cmd)

    #elfclass = re.findall('Class:\s*(.*$)', out, re.MULTILINE)[0]
    entrypoint = int(re.findall('Entry point address:\s*(.*$)', out, re.MULTILINE)[0], 16)

    return entrypoint

def no_frame_pointer(path):
    cmd = [_READELF, '-hWS', path]
    out = subprocess.check_output(cmd)

    #elfclass = re.findall('Class:\s*(.*$)', out, re.MULTILINE)[0]
    out = out.split('.eh_frame         PROGBITS        ')[1]
    out = out.split(" ")[2]

    return (int(out,16) > 4)



class ELF:
  '''A parsed ELF file'''
  cachedir = "cache" 

  def __init__(self, path, plt = True, base = 0x0):
    self.path = str(path)
    self.base = base
    self.sections = dict()

    self.entrypoint = entrypoint(path)
    self.no_frame_pointer = no_frame_pointer(path)
    #self._load_sections()
    
    
    if plt:
      self.plt, self.got = plt_got(self.path, self.base)
    else:
      self.plt, self.got = dict(), dict()
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
