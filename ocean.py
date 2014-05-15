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

import os
import argparse
import csv
import sys

from src.Process    import Process
from src.Detection  import GetArgs, GetFiles, GetCmd, GetDir
from src.Mutation   import BruteForceMutator, NullMutator, BruteForceExpander, SurpriseMutator ,InputMutator, RandomInputMutator
from src.Printer    import Printer

def readmodfile(modfile):
  hooked_mods = [] 
  if modfile is not None:
    hooked_mods =  open(modfile).read().split("\n")
    hooked_mods = filter(lambda x: x <> '', hooked_mods)
  return hooked_mods

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description='xxx')
    parser.add_argument("testcase", help="Testcase to use", type=str, default=None)
    parser.add_argument("mode", help="Print mode to use", type=str, default="split")
    #
    #parser.add_argument("outdir", help="Output directory to use", type=str, default=".")
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

    parser.add_argument("--X-program", dest="envs",
                        help="",
                        action="store_const", const=dict(DISPLAY=":0"), default=dict())

    parser.add_argument("-n", dest="max_mut", type=int,
                        help="", default=0)

    options = parser.parse_args()
    
    testcase = options.testcase
    print_mode = options.mode
    filters = options.filter_by
    incmodfile = options.inc_mods
    ignmodfile = options.ign_mods
    show_stdout = options.show_stdout
    max_mut = options.max_mut

    csvfile = sys.stdout

    os.chdir(GetDir(testcase))
    program = GetCmd(None)

    #os.system('ldd '+program)
    #exit(0)

    os.chdir("crash")

    envs = options.envs
    args = GetArgs()
    files = GetFiles()

    # modules to include or ignore
    included_mods = readmodfile(incmodfile)
    ignored_mods = readmodfile(ignmodfile) 
     
    #if modfile is not None:
    #  hooked_mods =  open(modfile).read().split("\n")
    #  hooked_mods = filter(lambda x: x <> '', hooked_mods) 
    
    original_inputs = InputMutator(args, files, NullMutator)
    #mutated_inputs  = InputMutator(args, files, BruteForceMutator)
    #expanded_inputs = InputMutator(args, files, BruteForceExpander)
    crazy_inputs    = RandomInputMutator(args, files, SurpriseMutator)

    app = Process(program, envs, included_mods, ignored_mods, no_stdout = not show_stdout )
    prt = Printer("/dev/stdout", program)
    map(prt.filter_by, filters)

    # unchanged input
    delta, original_input = original_inputs.next()
    original_events = app.getData(original_input)

    if original_events is None:
        print "Execution of",program,"failed!"
        exit(-1)

    prt.print_events("o", original_events, print_mode)

    for (i, (d, mutated)) in enumerate(crazy_inputs):
      if app.timeouted():
        sys.exit(-1)

      if i >= max_mut:
        break

      events = app.getData(mutated)
      prt.print_events(d, events, print_mode)


      # x = hash_events(events)
      #
      # if not (x in tests):
      #
      #   tests.add(x)
      #
      #   g = CallGraph(events)
      #   y = hash(str(g.graph.to_string()))
      #   #print y
      #
      #   if (not (y in tests)):
      #     name = "-".join(map(str, [delta["iname"], delta["mtype"],delta["aoffset"], delta["byte"]]))
      #     #print events[-1]
      #     g.WriteGraph(outdir+"/"+name+".dot")
      #     tests.add(y)


    #for delta, mutated in mutated_inputs:

    #  if app.timeouted():
    #    sys.exit(-1)

    #  events = app.getData(mutated)
    #  vec.vectorize(events)

