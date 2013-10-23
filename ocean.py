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
from ptrace.process_tools import dumpProcessInfo
from ptrace.tools import inverseDict
from ptrace.func_call import FunctionCallOptions
from ptrace.signames import signalName, SIGNAMES
from signal import SIGTRAP, SIGSEGV
from ptrace.terminal import enableEchoMode, terminalWidth
from errno import ESRCH, EPERM
from ptrace.cpu_info import CPU_POWERPC
from ptrace.debugger import ChildError
from ptrace.debugger.memory_mapping import readProcessMappings


from Detection import GetArgs, GetFiles, GetCmd, GetDir
#from Mutation  import RandomMutator, BruteForceMutator, CompleteMutator, InputMutator
from Mutation  import BruteForceMutator, InputMutator

from Event import Exit, Signal, StrncmpCall

from ELF import ELF
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

        # Parse ELF
        self.elf = ELF(self.program)

        self.last_signal = {}
        self.crashed = False
        self.events = []

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
                call =  StrncmpCall(name)
                call.DetectParams(self.process)
                return call
                #error("Stopped at %s" %
                #breakpoint.desinstall(set_ip=True)
        else:
          self.crashed = True
          return Signal(signal)
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

        self.events.append(self.createEvent(signal))


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
        #self.breakpoint(self.elf.FindFuncInPlt("strncmp"))
        #self.breakpoint(self.elf.FindFuncInPlt("strlen"))

        while True:
            if not self.debugger or self.crashed:
                # There is no more process: quit
                return

            try:
              self.cont()
            except ProcessExit, event:
              self.events.append(Exit(event.exitcode))

              pass
              #error(event)
              #self.nextProcess()

            #done = True
            #if done:
            #    return


    def getData(self, inputs):
        self.events = []
        self.debugger = PtraceDebugger()

        #try:
        self.runProcess([self.program]+inputs)
        #with open(self.outdir+"/"+self.name+".csv", "a+") as csvfile:
        #  eventwriter = csv.writer(csvfile, delimiter='\t', quotechar='\'')
        #  eventwriter.writerow(list(delta)+self.events)

        self.process.terminate()
        self.process.detach()

        self.process = None
        return self.events
        #for desc in self.ofiles:
        #  os.close(desc)
        #self.debugger.quit()

        #error("Quit gdb.")


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
    inputs = InputMutator(GetArgs(), GetFiles(), BruteForceMutator)


    app = App(program, no_stdout=no_stdout, outdir = outfile)
    stats = Stats()
    i = 10

    #app.getData(input.GetInput(), inputs.GetDelta())

    for delta, mutated in inputs:
      events = app.getData(mutated)
      stats.AddData(delta, events)

    xss = stats.Compute()

    if (outfile == "/dev/stdout"):
      csvfile = sys.stdout
    else:
      csvfile = open(outfile, "a+")

    csvwriter = csv.writer(csvfile, delimiter='\t', quotechar='\'')
    for xs in xss:
      csvwriter.writerow([testcase]+xs)

    #for i in range(100):
      #print inputs.GetInput()
      #app.getData(inputs.GetMutatedInput())
