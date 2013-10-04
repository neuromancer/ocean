#!/usr/bin/python

from ptrace import PtraceError
from ptrace.debugger import (PtraceDebugger, Application,
    ProcessExit, NewProcessEvent, ProcessSignal,
    ProcessExecution, ProcessError)
from optparse import OptionParser
from os import getpid
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
# Set the path to the executable to debug
#exe = sys.argv[1]

_READELF = '/usr/bin/readelf'
_OBJDUMP = '/usr/bin/objdump'

#def die(s):
#  print s
#  exit(-1)

#def check(f):
#  import os
#  if not (os.access(f, os.X_OK) and os.path.isfile(f)):
#    die('Executable %s needed for readelf.py, please install binutils' % f)
#
#check(_READELF)
#check(_OBJDUMP)
#
#def plt_got(path):
#  plt, got = dict(), dict()
#
#  cmd = [_OBJDUMP, '-d', path]
#  out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
#  got32 = '[^j]*jmp\s+\*0x(\S+)'
#  got64 = '[^#]*#\s+(\S+)'
#  lines = re.findall('([a-fA-F0-9]+)\s+<([^@<]+)@plt>:(%s|%s)' % (got32, got64), out)
#
#  for addr, name, _, gotaddr32, gotaddr64 in lines:
#     addr = int(addr, 16)
#     gotaddr = int(gotaddr32 or gotaddr64, 16)
#     plt[name] = addr
#     got[name] = gotaddr
#
#  return plt, got

#def symbols(file):
#    import re, subprocess
#    symbols = {}
#    # -s : symbol table
#    cmd = [_READELF, '-s', file]
#    out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
#    field = '\s+(\S+)'
#    lines = re.findall('^\s+\d+:' + field * 7 + '$', out, re.MULTILINE)
#
#    for addr, size, type, _bind, _vis, _ndx, name in lines:
#        addr = int(addr, 16)
#        size = int(size, 10)
#        if addr <> 0 and name <> '':
#            symbols[name] = {'addr': addr,
#                             'size': size,
#                             'type': type,
#                             }
#    return symbols

#plt, got = plt_got('/bin/ls')
#
#for symbol,val in plt.items():
#  print symbol, "0x%.8x" % val
#
#exit(0)

from ptrace import PtraceError
from ptrace.debugger import (PtraceDebugger, Application,
    ProcessExit, ProcessSignal, NewProcessEvent, ProcessExecution, Breakpoint)
from ptrace.syscall import (SYSCALL_NAMES, SYSCALL_PROTOTYPES,
    FILENAME_ARGUMENTS, SOCKET_SYSCALL_NAMES)
from ptrace.func_call import FunctionCallOptions
from sys import stderr, exit
from optparse import OptionParser
from logging import getLogger, error
from ptrace.syscall.socketcall_constants import SOCKETCALL
from ptrace.compatibility import any
from ptrace.error import PTRACE_ERRORS, writeError
from ptrace.ctypes_tools import formatAddress
import re

class Gdb(Application):
    def __init__(self):
        Application.__init__(self)

        # Parse self.options
        self.parseOptions()

        # Setup output (log)
        self.setupLog()

        self.last_signal = {}

        # We assume user wants all possible information
        self.syscall_options = FunctionCallOptions(
            write_types=True,
            write_argname=True,
            write_address=True,
        )

        # FIXME: Remove self.breaks!
        self.breaks = dict()

        self.followterms = []

    def setupLog(self):
        self._setupLog(stdout)

    def parseOptions(self):
        parser = OptionParser(usage="%prog [options] -- program [arg1 arg2 ...]")
        self.createCommonOptions(parser)
        self.createLogOptions(parser)
        self.options, self.program = parser.parse_args()

        if self.options.pid is None and not self.program:
            parser.print_help()
            exit(1)

        self.processOptions()
        self.show_pid = self.options.fork

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

        # Hit breakpoint?
        if signal.signum == SIGTRAP:
            ip = self.process.getInstrPointer()
            if not CPU_POWERPC:
                # Go before "INT 3" instruction
                ip -= 1
            breakpoint = self.process.findBreakpoint(ip)
            if breakpoint:
                error("Stopped at %s" % breakpoint)
                breakpoint.desinstall(set_ip=True)
        else:
            self.processSignal(signal)
        return None

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

    def runDebugger(self):
        self.setupDebugger()

        # Create new process
        try:
            self.process = self.createProcess()
        except ChildError, err:
            writeError(getLogger(), err, "Unable to create child process")
            return
        if not self.process:
            return

        # Trace syscalls
        self.invite = '(gdb) '
        self.previous_command = None

        self.breakpoint(0x08049950)

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
        try:
            self.runDebugger()
        except KeyboardInterrupt:
            error("Interrupt debugger: quit!")
        except PTRACE_ERRORS, err:
            writeError(getLogger(), err, "Debugger error")
        self.process = None
        self.debugger.quit()
        error("Quit gdb.")

if __name__ == "__main__":
    Gdb().main()
