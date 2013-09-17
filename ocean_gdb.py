#!/usr/bin/gdb -x

import sys
import gdb
import random

class Signal:
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)


class Syscall:
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)

class Call:
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)

## Events

catched_calls = [ 
                 "strcpy", "strcpy@plt", "strcpy@got.plt",
                 "strncpy", "strncpy@plt", "strncpy@got.plt",
                 "strlen", "strlen@plt", "strlen@got.plt",
                 "strcat", "strcat@plt", "strcat@got.plt",
                 # Memory manipulation                 
                 "memcpy", "memcpy@plt", "memcpy@got.plt"
                 ]

def CatchSyscalls():
  gdb.execute("catch syscall", to_string=True)

def CatchSignals():
  gdb.execute("handle all stop", to_string=True)

def CatchCalls():
  for f in catched_calls:
    gdb.execute("break "+f, to_string=True)

def GetSyscall(cs):
  if ("(returned from syscall " in cs):
    s = cs.split("(returned from syscall ")[1]
    s = s.split(")")[0]
    return Syscall(s)
  else:
    return None

def GetSignal(cs):
  if ("Program received signal " in cs):
    s = cs.split("Program received signal ")[1]
    s = s.split(",")[0]
    return Signal(s)
  else:
    return None

def GetCall(cs):
  if (any(map(lambda f: f in cs, catched_calls))):
    s = cs.split(" in ")[1]
    s = s.split(" (")[0]
    return Call(s)
  else:
    return None


## ??

def isCrash(e):
  return (str(e) == "SIGSEGV")


def isBadEIP():
  
  try:
    gdb.execute("x/i $eip", to_string=True)
    return True
  except gdb.error:
    return False  
   

## Analysis

def Init():
  gdb.execute("set breakpoint pending on", to_string=True)
  gdb.execute("unset environment", to_string=True)
  gdb.execute("set environment MALLOC_CHECK_ = 0", to_string=True)

  gdb.execute("break __libc_start_main", to_string=True) 
  gdb.execute("start", to_string=True)  


def getPath(size):
  
  r = []
  Init() 
  CatchSyscalls()
  CatchSignals()
  CatchCalls()
  e = None

  while True:
  
        #if not gdb.selected_inferior().is_valid():
    #  break
    try: 
      cs = gdb.execute("c", to_string=True)
      syscall = GetSyscall(cs) 
      signal  = GetSignal(cs)
      call    = GetCall(cs)
      e = str(gdb.parse_and_eval("$eip")).split(" ")[0]

      if (syscall <> None):
        r.append(syscall)
      if (call <> None):
        r.append(call)
      if (signal <> None):
        r.append(signal)

    except gdb.error:
       pass
    #  print e
    #  break
 
    if r <> []:
      if (isCrash(r[-1])):
        e = str(gdb.parse_and_eval("$eip")).split(" ")[0]
        print e

        break


    #addr = gdb.parse_and_eval("$eip")


    #raw_ins = gdb.execute("disassemble $eip,+1", to_string=True)
    #raw_ins = str(raw_ins)
    #print d
 
  return r

import csv
import random

#print sys.argv[0]

#Init()
#gdb.execute("run")
#print getPath(1)


with open('ocean.csv', 'wb') as csvfile:
  pathwriter = csv.writer(csvfile)
  path = getPath(1)
  pathwriter.writerow(path)

gdb.execute("quit", to_string=True)
