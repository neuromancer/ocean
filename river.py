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

import sys
import csv

from src.ELF  import ELF, load_plt_calls
from src.Spec import specs


if __name__ == "__main__":

  
  prog = sys.argv[1]
  outfile = sys.argv[2]

  cond_control_flow_ins = ["je","jz","jnz","jn","jg"]
  ncond_control_flow_ins = ["ret","jmp"]

  control_flow_ins = cond_control_flow_ins + ncond_control_flow_ins

  csv_writer = csv.writer(open(outfile,"a+"), delimiter="\t")
  inss = load_plt_calls(prog, control_flow_ins)
  r = [""]

  #print sys.argv[1]+"\t",
  for ins in inss:
    #print ins
    if ins[1] in cond_control_flow_ins:
      if not (r[-1] in ["cjmp","jmp"]):
        r.append("cjmp")
    if ins[1] in ncond_control_flow_ins:
      if not (r[-1] in ["jmp"]):       
        r.append("jmp")
    if ins[-1] in specs:
      r.append(ins[-1])
    #else:
    #  if not (r[-1] in ["call"]):
    #    r.append("call")
 
    #print r

  csv_writer.writerow([prog," ".join(r)])
  #elf = ELF(sys.argv[1])
  #elf._load_sections()
  #elf._load_instructions()
  #print elf.raw_instructions


