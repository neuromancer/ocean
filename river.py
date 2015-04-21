#!/usr/bin/python2

"""
This file is part of ocean.

SEA is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SEA is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SEA. If not, see <http://www.gnu.org/licenses/>.

Copyright 2014 by neuromancer
"""

import random
import time
import sys
import csv
import re

from src.ELF  import ELF, load_plt_calls, plt_got
from src.Spec import specs
#from src.Misc import readmodfile

if __name__ == "__main__":

  
  prog = sys.argv[1]
  #outfile = sys.argv[2]

  cond_control_flow_ins = ["jo", "jno", "js", "jns", "je",
                           "jz","jnz", "jb", "jnae", "jc", 
                           "jnb", "jae", "jnc", "jbe", "jna", 
                           "ja", "jnbe", "jl", "jnge", "jge", 
                           "jnl", "jle", "jng", "jg",  "jnle", 
                           "jp", "jpe", "jnp", "jpo", "jcxz", "jecxz"]

  ncond_control_flow_ins = ["ret","jmp","call"]

  control_flow_ins = cond_control_flow_ins + ncond_control_flow_ins

  #csv_writer = csv.writer(open(outfile,"a+"), delimiter="\t")
  plt, _ = plt_got(prog,0x0)

  # plt is inverted
  inv_plt = dict()

  for func, addr in plt.items():
    if func in specs:  # external functions are discarded
      inv_plt[addr] = func
    #else:
    #   print func, "discarded!"

  plt = inv_plt

  inss = load_plt_calls(prog, control_flow_ins)
  useful_inss_list = []
  useful_inss_dict = dict() 
  libc_calls = []
  #labels = dict()

  #print sys.argv[1]+"\t",
  for i,ins in enumerate(inss.split("\n")):

    # prefix removal
    ins = ins.replace("repz ","")
    ins = ins.replace("rep ","")

    pins = ins.split("\t")
    #print pins
    ins_addr = pins[0].replace(":","").replace(" ","")
    #print pins,ins_addr

    if len(pins) == 1 and ">" in ins: #label
      x = pins[0].split(" ")

      ins_addr = x[0]

      y = [i,ins_addr, None, None] 
      useful_inss_dict[ins_addr] = y
      useful_inss_list.append(y)

      #print "label:",y

    elif any(map( lambda x: x in ins, control_flow_ins)) and len(pins) == 3: # control flow instruction
      #print pins
      x = pins[2].split(" ")

      ins_nme = x[0]
      ins_jaddr = x[-2]

      
      #if ("" == ins_jaddr):
      #  print pins
      #print x
      #print ins_nme, ins_jaddr
      y = [i, ins_addr, ins_nme, ins_jaddr]
  
      useful_inss_dict[ins_addr] = y
      useful_inss_list.append(y)
  
      if "call" in pins[2]:
        if ins_jaddr <> '':
          func_addr = int(ins_jaddr,16)
          if func_addr in plt:
            libc_calls.append(i)

    else: # all other instructions 
      y = [i, ins_addr, None, None] 

      useful_inss_dict[ins_addr] = y
      useful_inss_list.append(y)

  #print useful_inss_list
  max_inss = len(useful_inss_list)
  traces = set()

  # exploration time!
  while(True):

    # resuling (sub)trace
    r = ""
    # starting point
    i = random.choice(libc_calls)
    j = 0

    r = prog+"\t"

    while True:

      # last instruction case
      if (i+j) == max_inss:
        break


      _,ins_addr,ins_nme,ins_jaddr = useful_inss_list[i+j]
    
      #print i+j,ins_nme, ins_jaddr

      if ins_nme == 'call': # ordinary call
        #"addr", ins_jaddr

        if ins_jaddr == '':
          break # parametric jmp, similar to ret for us

        ins_jaddr = int(ins_jaddr,16)
        if ins_jaddr in plt:
          r = r + " " + plt[ins_jaddr]
          if plt[ins_jaddr] == "exit":
            break
        else:

          if ins_jaddr in useful_inss_dict:
            r = r + " " + hex(ins_jaddr)
            i,_,_,_ = useful_inss_dict[ins_jaddr]
            j = 0
            continue

          else:
            pass # ignored call

      elif ins_nme == 'ret':
        break
      else:
        pass
        #print i+j,ins_nme, ins_jaddr

      #print j
      if ins_nme == 'jmp':

        if ins_jaddr in plt: # call equivalent using jmp
          r = r + " " + plt[jaddr]
        
        else:
          
          if ins_jaddr == '':
            break # parametric jmp, similar to ret for us

          ins_jaddr = int(ins_jaddr,16)
          if ins_jaddr in useful_inss_dict:
            r = r + " " + hex(ins_jaddr)
            i,_,_,_ = useful_inss_dict[ins_jaddr]
            j = 0
            continue

          else:
            pass # ignored call
  

      if ins_nme in cond_control_flow_ins:

        assert(ins_jaddr <> None)

        cond = random.randint(0,1)

        if cond == 1:
 
          i,_,_,_ = useful_inss_dict[ins_jaddr]
          j = 0
          continue
   
      j = j + 1

    x = hash(r)

    if x not in traces:
      print r
      traces.add(x)

    sys.stdout.flush()


  #explore(ri, useful_inss_list, useful_inss_dict)

  #for i in range(ri, ri + 30):
  #  print i,useful_inss_list[i]

  #for addr,(ins,jaddr) in useful_inss.items():
  #  if ins is not None:
  #    print addr+": "+ins+" -> "+jaddr

  #print libc_calls
  #print useful_inss[libc_calls[20]]
  #print useful_inss[20]

  #csv_writer.writerow([prog," ".join(r)])
  #elf = ELF(sys.argv[1])
  #elf._load_sections()
  #elf._load_instructions()
  #print elf.raw_instructions

