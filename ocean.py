#!/usr/bin/python2

import os
import argparse
import csv
import sys

from src.Process    import Process
from src.Detection  import GetArgs, GetFiles, GetCmd, GetDir
from src.Mutation   import BruteForceMutator, NullMutator, BruteForceExpander, InputMutator
from src.Vectorizer import vectorizer

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
    writer = csv.writer(csvfile, delimiter='\t')

    os.chdir(GetDir(testcase))
    program = GetCmd(None)
    os.chdir("crash")

    args = GetArgs()
    files = GetFiles()

    original_inputs = InputMutator(args, files, NullMutator)
    mutated_inputs  = InputMutator(args, files, BruteForceMutator)
    expanded_inputs = InputMutator(args, files, BruteForceExpander)

    tests = set()
    app = Process(program, no_stdout=no_stdout, outdir = None)

    # unchanged input
    delta, original_input = original_inputs.next()
    original_events = app.getData(original_input)

    #if not os.path.isdir(outdir):
    #  os.mkdir(outdir)

    #writer.writerow([program]+map(lambda (x,y): x+"="+y, original_events.items()))
    events = vectorizer(original_events)
    writer.writerow([program]+events)

    x = hash(tuple(events))
    tests.add(x)

    for delta, mutated in expanded_inputs:
      if app.timeouted():
        sys.exit(-1)

      events = app.getData(mutated)
      events = vectorizer(events)

      x = hash(tuple(events))
      if not (x in tests):
        tests.add(x)
        writer.writerow([program]+events)

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

    #vec.fit_transform(mes)
    #print vec.get_feature_names()

    for delta, mutated in mutated_inputs:

      if app.timeouted():
        sys.exit(-1)

      events = app.getData(mutated)
      events = vectorizer(events)

      x = hash(tuple(events))
      if not (x in tests):
        tests.add(x)
        #print events
        writer.writerow([program]+events)
