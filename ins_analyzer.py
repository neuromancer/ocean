#!/usr/bin/gdb -x

import sys
import gdb
import random

class Ins:
  def __init__(self, ins):
    self.raw_ins = str(ins)

  def __str__(self):
    return str(self.raw_ins)

class Signal:
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return str(self.name)


def CatchIns():
   gdb.execute("display/i $eip", to_string=True)

def CatchSignals():
  gdb.execute("handle all stop", to_string=True)

def GetIns(cs):
  if ("=> " in cs):
    s = cs.split(":\t")[1]
    s = s.replace("\n", "")
    if ("cmp" in s):
      return Ins(s)
    else:
      return None
  else:
    return None

def GetSignal(cs):
  if ("Program received signal " in cs):
    s = cs.split("Program received signal ")[1]
    s = s.split(",")[0]
    return Signal(s)
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

  gdb.execute("break main", to_string=True) 
  gdb.execute("display/i $eip", to_string=True)  
  gdb.execute("start", to_string=True)  

def Step():
  return gdb.execute("si", to_string=True)

def getPath(size):
  
  r = []
  Init() 
  e = None

  while True:
  
        #if not gdb.selected_inferior().is_valid():
    #  break
    try: 
      cs = Step()
      ins = GetIns(cs) 
      signal  = GetSignal(cs)

      e = str(gdb.parse_and_eval("$eip")).split(" ")[0]

      if (ins <> None):
        r.append(ins)
      elif (signal <> None):
        r.append(signal)

     
    except gdb.error:
       print "\n".join(map(str,r))
       #print r
       break
    #  print e
    #  break
 
    if r <> []:
      if (isCrash(r[-1])):
        e = str(gdb.parse_and_eval("$eip")).split(" ")[0]
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
