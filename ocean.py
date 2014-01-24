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
from src.Mutation   import BruteForceMutator, NullMutator, BruteForceExpander, SurpriceMutator ,InputMutator, RandomInputMutator
from src.Vectorizer import Vectorizer

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description='xxx')
    parser.add_argument("testcase", help="Testcase to use", type=str, default=None)
    #parser.add_argument("outdir", help="Output directory to use", type=str, default=".")
    parser.add_argument("--no-stdout",
                        help="Use /dev/null as stdout/stderr, or close stdout and stderr if /dev/null doesn't exist",
                        action="store_true", default=False)

    parser.add_argument("--identify",
                        help="No mutations are performed, only the original input is processed",
                        action="store_true", default=False)

    options = parser.parse_args()
    testcase = options.testcase
    #outdir = options.outdir
    no_stdout = options.no_stdout
    identify_mode = options.identify

    csvfile = sys.stdout

    os.chdir(GetDir(testcase))
    program = GetCmd(None)
    os.chdir("crash")

    args = GetArgs()
    files = GetFiles()

    original_inputs = InputMutator(args, files, NullMutator)
    mutated_inputs  = InputMutator(args, files, BruteForceMutator)
    expanded_inputs = InputMutator(args, files, BruteForceExpander)
    crazy_inputs    = RandomInputMutator(args, files, SurpriceMutator)

    app = Process(program, no_stdout=no_stdout, outdir = None)
    vec = Vectorizer("/tmp/test.csv", program)

    # unchanged input
    delta, original_input = original_inputs.next()
    original_events = app.getData(original_input)
    #exit(0)

    #if not os.path.isdir(outdir):
    #  os.mkdir(outdir)

    #writer.writerow([program]+map(lambda (x,y): x+"="+y, original_events.items()))
    vec.vectorize(original_events)
    #assert(0)
    #events = vectorizer(original_events)
    #writer.writerow([program]+events)
    max_mut = 3000

    for (i, (_, mutated)) in enumerate(expanded_inputs):
      if app.timeouted():
        sys.exit(-1)

      events = app.getData(mutated)
      vec.vectorize(events)

      if i > max_mut:
        break

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

