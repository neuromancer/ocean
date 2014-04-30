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
from src.Vectorizer import Vectorizer

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description='xxx')
    parser.add_argument("testcase", help="Testcase to use", type=str, default=None)
    #parser.add_argument("outdir", help="Output directory to use", type=str, default=".")
    parser.add_argument("--show-stdout",
                        help="Don't use /dev/null as stdout/stderr, nor close stdout and stderr if /dev/null doesn't exist",
                        action="store_true", default=False)

    #parser.add_argument("--identify",
    #                    help="No mutations are performed, only the original input is processed",
    #                    action="store_true", default=False)

    parser.add_argument("--X-program", dest="envs",
                        help="",
                        action="store_const", const=dict(DISPLAY=":0"), default=dict())

    #parser.add_argument("--raw-mode", dest="raw",
    #                    help="",
    #                    action="store_true", default=False)

    #parser.add_argument("--header", dest="header",
    #                    help="",
    #                    action="store_true", default=False)

    parser.add_argument("-n", dest="max_mut", type=int,
                        help="", default=0)

    options = parser.parse_args()
    testcase = options.testcase
    #outdir = options.outdir
    show_stdout = options.show_stdout
    #identify_mode = options.identify
    #raw_mode = options.raw
    #write_header = options.header
    max_mut = options.max_mut

    csvfile = sys.stdout

    os.chdir(GetDir(testcase))
    program = GetCmd(None)
    os.chdir("crash")

    envs = options.envs
    args = GetArgs()
    files = GetFiles()

    original_inputs = InputMutator(args, files, NullMutator)
    #mutated_inputs  = InputMutator(args, files, BruteForceMutator)
    #expanded_inputs = InputMutator(args, files, BruteForceExpander)
    crazy_inputs    = RandomInputMutator(args, files, SurpriseMutator)

    app = Process(program, envs, no_stdout= not show_stdout )
    vec = Vectorizer("/dev/stdout", program, True)

    #if write_header:
    #  vec.write_header()
    #  exit(0)

    # unchanged input
    delta, original_input = original_inputs.next()
    original_events = app.getData(original_input)

    if original_events is None:
        print "Execution of",program,"failed!"
        exit(-1)

    #exit(0)

    #if not os.path.isdir(outdir):
    #  os.mkdir(outdir)

    #writer.writerow([program]+map(lambda (x,y): x+"="+y, original_events.items()))
    vec.vectorize(original_events)
    #assert(0)
    #events = vectorizer(original_events)
    #writer.writerow([program]+events)


    for (i, (_, mutated)) in enumerate(crazy_inputs):
      if app.timeouted():
        sys.exit(-1)

      if i >= max_mut:
        break

      events = app.getData(mutated)
      vec.vectorize(events)


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

