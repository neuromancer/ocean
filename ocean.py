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
from ptrace.version import VERSION, WEBSITE
from ptrace.error import PTRACE_ERRORS, writeError
from ptrace.binding import HAS_PTRACE_SINGLESTEP
from ptrace.disasm import HAS_DISASSEMBLER
from ptrace.ctypes_tools import (truncateWord,
    formatWordHex, formatAddress, formatAddressRange, word2bytes)

from ptrace.signames import signalName, SIGNAMES
from signal import SIGTRAP, SIGALRM, signal, alarm
from ptrace.terminal import enableEchoMode, terminalWidth
from errno import ESRCH, EPERM
from ptrace.cpu_info import CPU_POWERPC
from ptrace.debugger import ChildError

from Detection import GetArgs, GetFiles, GetCmd, GetDir
from Mutation  import BruteForceMutator, NullMutator, BruteForceExpander, InputMutator

from Event import Exit, Timeout, Crash, Signal, Call, specs

from ELF import ELF
from Status import TimeoutEx, alarm_handler
from Run import Launch
from Stats import Stats

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
        else:
          self.crashed = True
          #regs = self.process.getregs()
          #for name, type in regs._fields_:
          #  value = getattr(regs, name)
          #  print name, "->", hex(value),

          #p = self.process.getInstrPointer()
          #print "eip ->", hex(p)
          return Crash(self.process)
          #return Signal(signal)
          #self.processSignal(signal)
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

        # Create new process
        try:
            self.process = self.createProcess(cmd, self.no_stdout)
            self.crashed = False
        except ChildError, err:
            writeError(getLogger(), err, "Unable to create child process")
            return
        if not self.process:
            return


        # Set the breakpoints

        for func_name in self.elf.GetFunctions():
          if func_name in specs:
            self.breakpoint(self.elf.FindFuncInPlt(func_name))
          #elif func_name.lstrip("_") in specs:
          #  self.breakpoint(self.elf.FindFuncInPlt(func_name.lstrip("_")))
        #assert(0)

        #self.breakpoint(self.elf.FindFuncInPlt("strncmp"))
        #self.breakpoint(self.elf.FindFuncInPlt("strlen"))

        signal(SIGALRM, alarm_handler)
        timeout = 5
        alarm(timeout)

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

        except TimeoutEx:
          self.events.append(Timeout(timeout))
          self.timeouts += 1
          return



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

    options = parser.parse_args()
    testcase = options.testcase
    outfile = options.outdir
    no_stdout = options.no_stdout


    os.chdir(GetDir(testcase))
    program = GetCmd(None)
    os.chdir("crash")

    args = GetArgs()
    files = GetFiles()

    original_inputs = InputMutator(args, files, NullMutator)
    mutated_inputs  = InputMutator(args, files, BruteForceMutator)
    expanded_inputs = InputMutator(args, files, BruteForceExpander)

    fields = []
    app = App(program, no_stdout=no_stdout, outdir = outfile)


    #app.getData(input.GetInput(), inputs.GetDelta())

    # unchanged input
    delta, original_input = original_inputs.next()
    original_events = app.getData(original_input)

    #print "Original test case:"
    #for event in original_events:
    #  print event,
    #print ""


    stats = Stats(original_events)
    #assert(0)

    for delta, mutated in expanded_inputs:
      events = app.getData(mutated)

      #print delta,
      #for e in events:
      #  print str(e),
      #print ""

      if app.timeouted():
        sys.exit(-1)
      #print map(repr, mutated)
      stats.AddData(delta, events)
      #assert(0)

    exit(0)

    #xss = stats.Compute()

    #if (outfile == "/dev/stdout"):
    #  csvfile = sys.stdout
    #else:
    #  csvfile = open(outfile, "a+")

    #csvwriter = csv.writer(csvfile, delimiter='\t', quotechar='\'')
    #for xs in xss:
    #  csvwriter.writerow([testcase]+xs)

    #for i in range(100):
      #print inputs.GetInput()
      #app.getData(inputs.GetMutatedInput())
