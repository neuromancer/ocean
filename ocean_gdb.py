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


def getPath(size):
  
  r = []
  gdb.execute("break __libc_start_main", to_string=True)

  gdb.execute("start", to_string=True)  
  gdb.execute("break __kernel_vsyscall", to_string=True)
  e = None

  while True:
  
    gdb.execute("c", to_string=True)
    #if not gdb.selected_inferior().is_valid():
    #  break
    try: 
      d = str(gdb.parse_and_eval("$eax")).split(" ")[0]
      e = str(gdb.parse_and_eval("$eip")).split(" ")[0]

      r.append(d)
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
print getPath(1)


#with open('ocean.csv', 'wb') as csvfile:
#  pathwriter = csv.writer(csvfile)
#  path = getPath(1)

#  pathwriter.writerow(path)


#gdb.execute("quit", to_string=True)
