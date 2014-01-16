from ptrace import PtraceError
from ptrace.debugger import (PtraceDebugger, Application,
    ProcessExit, NewProcessEvent, ProcessSignal,
    ProcessExecution, ProcessError)

from logging import getLogger, info, warning, error
from ptrace.error import PTRACE_ERRORS, writeError
from ptrace.disasm import HAS_DISASSEMBLER
from ptrace.ctypes_tools import (truncateWord,
    formatWordHex, formatAddress, formatAddressRange, word2bytes)

from ptrace.signames import signalName, SIGNAMES
from signal import SIGTRAP, SIGALRM, SIGABRT, SIGSEGV, SIGCHLD, SIGWINCH, SIGFPE, signal, alarm
from errno import ESRCH, EPERM
from ptrace.cpu_info import CPU_POWERPC
from ptrace.debugger import ChildError

from Event import Exit, Abort, Timeout, Crash, Signal, Call, specs, hash_events

from ELF import ELF
from Run import Launch
from MemoryMap import MemoryMaps

class Process(Application):
    def __init__(self, program, outdir, no_stdout = False):

        Application.__init__(self)  # no effect

        self.program = str(program)
        self.name = self.program.split("/")[-1]
        self.outdir = str(outdir)
        self.no_stdout = no_stdout

        self.process = None
        self.pid = None
        self.timeouts = 0
        self.max_timeouts = 10

        # Parse ELF
        self.elf = ELF(self.program)

        self.last_signal = {}
        self.last_call = None
        self.crashed = False
        self.events = []

        # FIXME: Remove self.breaks!
        #self.breaks = dict()

        #self.followterms = []


    def createEvents(self, signal):

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
                  #last_call = self.events[-1]
                  assert(self.last_call <> None)
                  #print breakpoint.address, self.last_call.GetReturnAddr()

                  breakpoint.desinstall(set_ip=True)
                  if (breakpoint.address == self.last_call.GetReturnAddr()):
                    self.last_call.DetectReturnValue(self.process)
                  else:
                    pass # FIXME: Why this could happen?

                  return []

                else:
                  call = Call(name)
                  self.mm  = MemoryMaps(self.program, self.pid)

                  call.DetectParams(self.process, self.mm)
                  self.last_call = call
                  self.breakpoint(call.GetReturnAddr())
                  return [call]

        elif signal.signum == SIGABRT:
          self.crashed = True
          return [Signal("SIGABRT"),Abort()]

        elif signal.signum == SIGSEGV:
          self.crashed = True
          return [Signal("SIGSEGV"), Crash(self.process, signal.getSignalInfo()._sifields._sigfault._addr)]

        elif signal.signum == SIGFPE:
          self.crashed = True
          return [Signal("SIGFPE"), Crash(self.process)]

        elif signal.signum == SIGCHLD:
          self.crashed = True
          return [Signal("SIGCHLD"), Crash(self.process)]

        # Harmless signals
        elif signal.signum == SIGWINCH:
          return [] # User generated, ignore.

        else:
          print "I don't know what to do with this signal:", str(signal)
          assert(False)

        return []


    def createProcess(self, cmd, no_stdout):

        self.pid = Launch(cmd, no_stdout, dict())
        #self.ofiles = list(files)
        is_attached = True

        try:
            return self.debugger.addProcess(self.pid, is_attached=is_attached)
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
        events = self.createEvents(signal)

        self.events = self.events + events


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
            #self.mm  = MemoryMaps(self.program, self.pid)
            #print self.mm
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
          #print "OSError!"
          self.events.append(Timeout(timeout))
          self.timeouts += 1
          return

        except IOError:
          #print "IOError!"
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
