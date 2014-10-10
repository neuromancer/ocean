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

""" 
Dedicated to the intelligence and beauty of a woman that
inspired this code despite of the distance..
"""


import os
import argparse
import csv
import sys
import random

from src.Process    import Process
from src.Detection  import GetArgs, GetFiles, GetCmd, GetDir
from src.Mutation   import NullMutator, RandomByteMutator, RandomExpanderMutator, RandomInputMutator
from src.Printer    import TypePrinter
from src.Event      import IsTimeout

def readmodfile(modfile):
  hooked_mods = [] 
  if modfile is not None:
    hooked_mods =  open(modfile).read().split("\n")
    hooked_mods = filter(lambda x: x <> '', hooked_mods)
  return hooked_mods

def prepare_inputs(inputs):
  r = []
  for input in inputs:
    arg = input.PrepareData()
    if not (arg is None):
      r.append(arg)

  return r

if __name__ == "__main__":

    if open("/proc/sys/kernel/randomize_va_space").read().strip() <> "0":
        print "Address space layout randomization (ASLR) is enabled, disable it before continue"
        print "Hint: # echo 0 > /proc/sys/kernel/randomize_va_space"
        sys.exit(-1)

    # Random seed initialziation
    random.seed()
    
    # Arguments
    parser = argparse.ArgumentParser(description='xxx')
    parser.add_argument("testcase", help="Testcase to use", type=str, default=None)
    parser.add_argument("--show-stdout",
                        help="Don't use /dev/null as stdout/stderr, nor close stdout and stderr if /dev/null doesn't exist",
                        action="store_true", default=False)
  
    parser.add_argument("--inc-mods",
                        help="",
                        type=str, default=None)
    
    parser.add_argument("--ign-mods",
                        help="",
                        type=str, default=None) 
 
    parser.add_argument("--filter-by",
                        help="",
                        type=str, nargs='+', default=[])

    parser.add_argument("--timeout", dest="timeout", type=int,
                        help="Timeout (in seconds)", default=3)

    parser.add_argument("-n", dest="max_mut", type=int,
                        help="", default=0)

    parser.add_argument("-d", dest="depth", type=int,
                        help="", default=1)
   
    parser.add_argument("-w", dest="width", type=int,
                        help="", default=0)

    options = parser.parse_args()
    
    testcase = options.testcase
    
    filters = options.filter_by
    incmodfile = options.inc_mods
    ignmodfile = options.ign_mods
    show_stdout = options.show_stdout
    max_mut = options.max_mut
    depth = options.depth
    width = options.width

    csvfile = sys.stdout

    os.chdir(GetDir(testcase))
    program = GetCmd(None)

    os.chdir("crash")

    timeout = options.timeout
    envs = dict()
    args = GetArgs()
    files = GetFiles()

    # modules to include or ignore
    included_mods = readmodfile(incmodfile)
    ignored_mods = readmodfile(ignmodfile) 
        
    original_inputs = RandomInputMutator(args + files, NullMutator)
    expanded_input_generator = RandomInputMutator(args + files, RandomExpanderMutator)
    mutated_input_generator = RandomInputMutator(args + files, RandomByteMutator)

    app = Process(program, envs, timeout, included_mods, ignored_mods, no_stdout = not show_stdout )
    
    prt = TypePrinter("/dev/stdout", program)

    # unchanged input
    null_mutt, original_input = original_inputs.next()
    original_events = app.getData(prepare_inputs(original_input))

    if original_events is None:
        print "Execution of",program,"failed!"
        exit(-1)

    #prt.set_original_events(original_events)
    prt.print_events(null_mutt, original_events)

    for (i, (d, mutated)) in enumerate(expanded_input_generator):
      #if app.timeouted():
      #  sys.exit(-1)

      if i >= max_mut:
        break

      events = app.getData(prepare_inputs(mutated))
      prt.print_events(d, events)
      
    mutated_inputs = []


    if depth > 0:
      for _ in range(width):
        _, mutated = mutated_input_generator.next()

        events = app.getData(prepare_inputs(mutated))
        prt.print_events(d, events)
        #print(map(str,mutated))#, map(type, mutated))
        if not IsTimeout(events[-1]):
          mutated_inputs.append(mutated)

    for _ in range(depth):
      for mutated_input in mutated_inputs:
        expanded_input_generator = RandomInputMutator(mutated_input, RandomExpanderMutator)
    
        for (i, (d, mutated)) in enumerate(expanded_input_generator):
          #if app.timeouted():
          #  sys.exit(-1)

          if i >= max_mut:
            break

          events = app.getData(prepare_inputs(mutated))
          prt.print_events(d, events)
