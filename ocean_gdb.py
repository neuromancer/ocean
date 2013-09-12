#!/usr/bin/gdb -x

import sys
import gdb
import random

#def parse_jmp_addr(raw_ins):
#  jmp = raw_ins.split("\n")[1].split("\t")[1].split("<")[0]
#  addr = jmp.split(" ")[-2]

#  return addr

#def getRandomData(values, size):
#  data = ""
#  value_size = len(values)
#  for i in range(size):
#    data = data + values[random.randint(0,value_size-1)]

#  return data

#def setData(data, data_addr, size, size_addr):

#  assert(len(data) == size)
#  gdb.execute("set *(int*) ("+size_addr+") = (int) "+str(size)) #

#  for i in range(size):
    #print "set *(char*) ("+data_addr+"+"+str(i)+") = (char) "+str(ord(data[i]))
#    gdb.execute("set *(char*) ("+data_addr+"+"+str(i)+") = (char) "+str(ord(data[i])))

#def Init():
#  gdb.execute("unset environment", to_string=True)

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
    return s
  else:
    return ""

def GetSignal(cs):
  if ("Program received signal " in cs):
    s = cs.split("Program received signal ")[1]
    s = s.split(",")[0]
    return s
  else:
    return ""

def GetCall(cs):
  if (any(map(lambda f: f in cs, catched_calls))):
    s = cs.split(" in ")[1]
    s = s.split(" (")[0]
    return s
  else:
    return ""


def getPath(size):
  
  r = []
  gdb.execute("set breakpoint pending on", to_string=True)
  gdb.execute("unset environment", to_string=True)
  gdb.execute("set environment MALLOC_CHECK_ = 0", to_string=True)

  gdb.execute("break __libc_start_main", to_string=True) 
  gdb.execute("start", to_string=True)  
  
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
      #d = str(gdb.parse_and_eval("$eax")).split(" ")[0]
      e = str(gdb.parse_and_eval("$eip")).split(" ")[0]

      if (syscall <> ''):
        r.append(syscall)
      if (call <> ''):
        r.append(call)
      if (signal <> ''):
        r.append(signal)
    except gdb.error:
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
