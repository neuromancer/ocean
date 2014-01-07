#!/usr/bin/python


import os
import argparse
import csv
import sys

from ptrace import PtraceError
from ptrace.debugger import (PtraceDebugger, Application,
    ProcessExit, NewProcessEvent, ProcessSignal,
    ProcessExecution, ProcessError)

from sys import stdout, stderr, exit
from logging import getLogger, info, warning, error
from ptrace.error import PTRACE_ERRORS, writeError
from ptrace.binding import HAS_PTRACE_SINGLESTEP
from ptrace.disasm import HAS_DISASSEMBLER
from ptrace.ctypes_tools import (truncateWord,
    formatWordHex, formatAddress, formatAddressRange, word2bytes)

from ptrace.signames import signalName, SIGNAMES
from signal import SIGTRAP, SIGALRM, SIGABRT, SIGSEGV, SIGCHLD, SIGWINCH, SIGUSR2, signal, alarm
from errno import ESRCH, EPERM
from ptrace.cpu_info import CPU_POWERPC
from ptrace.debugger import ChildError

from Detection import GetArgs, GetFiles, GetCmd, GetDir
from Mutation  import BruteForceMutator, NullMutator, BruteForceExpander, InputMutator

from Event import Exit, Abort, Timeout, Crash, Signal, Call, specs, hash_events

from ELF import ELF
from Status import TimeoutEx, alarm_handler
from Run import Launch
from Graph import CallGraph

class App(Application):
    def __init__(self, program, outdir, no_stdout = False):

        Application.__init__(self)  # no effect

        self.program = str(program)
        self.name = self.program.split("/")[-1]
        self.outdir = str(outdir)
        self.no_stdout = no_stdout

        self.process = None
        self.timeouts = 0
        self.max_timeouts = 10

        # Parse ELF
        self.elf = ELF(self.program)

        self.last_signal = {}
        self.crashed = False
        self.events = []
        #self.callstack = []

        # FIXME: Remove self.breaks!
        self.breaks = dict()

        self.followterms = []

        #with open(self.outdir+"/"+self.name+".csv", "w+") as f:
        #  f.write("")


    def createEvent(self, signal):

        # Hit breakpoint?
        if signal.signum == SIGTRAP:
            ip = self.process.getInstrPointer()
            if not CPU_POWERPC:
                # Go before "INT 3" instruction
                ip -= 1
            breakpoint = self.process.findBreakpoint(ip)
            if breakpoint:
                name = self.elf.FindAddrInPlt(breakpoint.address)

                if name is None:
                  last_call = self.events[-1]
                  assert(breakpoint.address == last_call.GetReturnAddr())

                  breakpoint.desinstall(set_ip=True)
                  last_call.DetectReturnValue(self.process)
                  return None

                else:

                  call = Call(name)
                  call.DetectParams(self.process)
                  self.breakpoint(call.GetReturnAddr())

                  #call.DetectParams(self.process)
                  return call
                  #error("Stopped at %s" %
                  #breakpoint.desinstall(set_ip=True)
        elif signal.signum == SIGABRT:
          self.crashed = True
          return Abort()

        elif signal.signum == SIGSEGV:
          self.crashed = True
          return Crash(self.process, signal.getSignalInfo()._sifields._sigfault._addr)

        elif signal.signum == SIGCHLD:
          self.crashed = True
          return Crash(self.process)

        # Harmless signals
        elif signal.signum == SIGWINCH:
          return None

        else:
          print "I don't know what to do with this signal:", str(signal)
          assert(False)

        return None



    def createProcess(self, cmd, no_stdout):

        pid = Launch(cmd, no_stdout, dict())
        #self.ofiles = list(files)
        is_attached = True

        try:
            return self.debugger.addProcess(pid, is_attached=is_attached)
        except (ProcessExit, PtraceError), err:
            if isinstance(err, PtraceError) \
            and err.errno == EPERM:
                error("ERROR: You are not allowed to trace process %s (permission denied or process already traced)" % pid)
            else:
                error("ERROR: Process can no be attached! %s" % err)
        return None

    def destroyProcess(self, signum, frame):
        assert(self.process is not None)
        print signum
        print frame

        #self.debugger.deleteProcess(self.process)
        #self.process.(SIGUSR2)
        print "end!"
        #self.process.detach()


    def _continueProcess(self, process, signum=None):
        if not signum and process in self.last_signal:
            signum = self.last_signal[process]

        if signum:
            error("Send %s to %s" % (signalName(signum), process))
            process.cont(signum)
            try:
                del self.last_signal[process]
            except KeyError:
                pass
        else:
            process.cont()

    def cont(self, signum=None):
        for process in self.debugger:
            process.syscall_state.clear()
            if process == self.process:
                self._continueProcess(process, signum)
            else:
                self._continueProcess(process)

        # Wait for a process signal
        signal = self.debugger.waitSignals()
        process = signal.process
        event = self.createEvent(signal)

        if event is not None:
          self.events.append(event)


    def readInstrSize(self, address, default_size=None):
        if not HAS_DISASSEMBLER:
            return default_size
        try:
            # Get address and size of instruction at specified address
            instr = self.process.disassembleOne(address)
            return instr.size
        except PtraceError, err:
            warning("Warning: Unable to read instruction size at %s: %s" % (
                formatAddress(address), err))
            return default_size

    def breakpoint(self, address):

        # Create breakpoint
        size = self.readInstrSize(address)
        try:
            bp = self.process.createBreakpoint(address, size)
        except PtraceError, err:
            return "Unable to set breakpoint at %s: %s" % (
                formatAddress(address), err)
        #error("New breakpoint: %s" % bp)
        return None

    def runProcess(self, cmd):

        #print ".",

        signal(SIGALRM, lambda s,a: ())
        timeout = 3
        alarm(timeout)

        # Create new process
        try:
            self.process = self.createProcess(cmd, self.no_stdout)
            self.crashed = False
        except ChildError, err:
            writeError(getLogger(), err, "Unable to create child process")
            return
        except OSError, err:
            writeError(getLogger(), err, "Unable to create child process")
            return

        except IOError, err:
            writeError(getLogger(), err, "Unable to create child process")
            return

        if not self.process:
            return


        # Set the breakpoints

        for func_name in self.elf.GetFunctions():
          if func_name in specs:
            self.breakpoint(self.elf.FindFuncInPlt(func_name))

        try:
          while True:
            if not self.debugger or self.crashed:
                # There is no more process: quit
                return

            self.cont()

          alarm(0)

        except ProcessExit, event:
          alarm(0)
          self.events.append(Exit(event.exitcode))
          return

        except OSError:
          print "OSError!"
          self.events.append(Timeout(timeout))
          self.timeouts += 1
          return

        except IOError:
          print "IOError!"
          self.events.append(Timeout(timeout))
          self.timeouts += 1
          return

        #except TimeoutEx:
        #   self.events.append(Timeout(timeout))
        #   self.timeouts += 1
        #   return



    def getData(self, inputs):
        self.events = []
        self.debugger = PtraceDebugger()

        self.runProcess([self.program]+inputs)

        self.process.terminate()
        self.process.detach()

        self.process = None
        return self.events


    def timeouted(self):
        return self.timeouts >= self.max_timeouts

if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description='xxx')
    parser.add_argument("testcase", help="Testcase to use", type=str, default=None)
    parser.add_argument("outdir", help="Output directory to use", type=str, default=".")
    parser.add_argument("--no-stdout",
                        help="Use /dev/null as stdout/stderr, or close stdout and stderr if /dev/null doesn't exist",
                        action="store_true", default=False)

    parser.add_argument("--identify",
                        help="No mutations are performed, only the original input is processed",
                        action="store_true", default=False)

    options = parser.parse_args()
    testcase = options.testcase
    outdir = options.outdir
    no_stdout = options.no_stdout
    identify_mode = options.identify


    os.chdir(GetDir(testcase))
    program = GetCmd(None)
    os.chdir("crash")

    args = GetArgs()
    files = GetFiles()

    original_inputs = InputMutator(args, files, NullMutator)
    mutated_inputs  = InputMutator(args, files, BruteForceMutator)
    expanded_inputs = InputMutator(args, files, BruteForceExpander)

    tests = set()
    app = App(program, no_stdout=no_stdout, outdir = outdir)

    # unchanged input
    delta, original_input = original_inputs.next()
    original_events = app.getData(original_input)

    if not os.path.isdir(outdir):
      os.mkdir(outdir)

    x = hash_events(original_events)
    tests.add(x)

    name = "ori"
    g = CallGraph(original_events)

    y = hash(str(g.graph.to_string()))
    tests.add(y)

    # if identify_mode:
    #   print program + "\t" +  str(original_events[-1])
    #   g.WriteGraph(outdir+"/"+name+".dot")
    #   exit(0)

    print original_events[-1]
    #g.WriteGraph(outdir+"/"+name+".dot")

    for delta, mutated in expanded_inputs:
      events = app.getData(mutated)

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


      #if app.timeouted():
      #  sys.exit(-1)

    for delta, mutated in mutated_inputs:
      events = app.getData(mutated)

      # x = hash_events(events)
      #
      # if not (x in tests):
      #
      #   tests.add(x)
      #
      #   g = CallGraph(events)
      #   y = hash(str(g.graph.to_string()))
      #
      #   if (not y in tests):
      #     name = "-".join(map(str, [delta["iname"], delta["mtype"],delta["aoffset"], delta["byte"]]))
      #     print events[-1]
      #     g.WriteGraph(outdir+"/"+name+".dot")
      #     tests.add(y)

      #if app.timeouted():
      #  sys.exit(-1)

