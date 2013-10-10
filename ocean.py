#!/usr/bin/python


import os
import argparse

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
from signal import SIGTRAP, SIGINT
from ptrace.terminal import enableEchoMode, terminalWidth
from errno import ESRCH
from ptrace.cpu_info import CPU_POWERPC
from ptrace.debugger import ChildError
from ptrace.debugger.memory_mapping import readProcessMappings


from Detection import GetArgs, GetFiles, GetCmd, GetDir
from Mutation  import RandomMutator, BruteForceMutator, CompleteMutator, InputMutator

from Event import StrncmpCall

from ELF import ELF
from Run import Launch

class App(Application):
    def __init__(self):

        Application.__init__(self)  # no effect

        # Parse self.options
        self.parseOptions()

        #self.input = None
        self.last_signal = {}
        self.events = []

        # FIXME: Remove self.breaks!
        self.breaks = dict()

        self.followterms = []

    def parseOptions(self):
        parser = argparse.ArgumentParser(description='xxx')
        parser.add_argument("testcase", help="", type=str, default=None)
        self.options = parser.parse_args()
        print self.options.testcase

    def detectTestcase(self):

        dirf = GetDir(self.options.testcase)
        os.chdir(dirf)
        program = GetCmd(None)
        os.chdir("crash")
        #print GetArgs()
        return program, InputMutator(GetArgs(), GetFiles(), BruteForceMutator)

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
            pass
            #self.processSignal(signal)
        return None



    def createProcess(self, cmd, no_stdout):

        pid = Launch(cmd, no_stdout, dict())
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
        error("New breakpoint: %s" % bp)
        return None

    def runProcess(self, cmd, no_stdout):
        #self.setupDebugger()

        # Create new process
        try:
            self.process = self.createProcess(cmd, no_stdout)
        except ChildError, err:
            writeError(getLogger(), err, "Unable to create child process")
            return
        if not self.process:
            return

        # Parse ELF
        #self.elf = ELF(self.program[0])

        # Set the breakpoints
        self.breakpoint(self.elf.FindFuncInPlt("strncmp"))
        #self.breakpoint(self.elf.FindFuncInPlt("strlen"))

        while True:
            if not self.debugger:
                # There is no more process: quit
                return

            try:
              self.cont()
            except ProcessExit, event:
              error(event)
              #self.nextProcess()

            #done = True
            #if done:
            #    return


    def main(self):
        self.debugger = PtraceDebugger()
        program, inputs = self.detectTestcase()

        # Parse ELF
        self.elf = ELF(program)
        #print inputs.GetMutatedInput()
        #print [program]
        no_stdout = False

        #try:
        self.runProcess([program, inputs.GetMutatedInput()], no_stdout)
        for event in self.events:
          print event.GetVector()
        #except KeyboardInterrupt:
        #    error("Interrupt debugger: quit!")
        #except PTRACE_ERRORS, err:
        #    writeError(getLogger(), err, "Debugger error")

        self.process = None
        self.debugger.quit()
        error("Quit gdb.")

if __name__ == "__main__":
    App().main()
