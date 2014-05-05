from ptrace import PtraceError
from ptrace.debugger import (PtraceDebugger, Application,
    ProcessExit, NewProcessEvent, ProcessSignal,
    ProcessExecution, ProcessError)

from logging import getLogger, info, warning, error
from ptrace.error import PTRACE_ERRORS, PtraceError, writeError
from ptrace.disasm import HAS_DISASSEMBLER
from ptrace.ctypes_tools import (truncateWord,
    formatWordHex, formatAddress, formatAddressRange, word2bytes)

from ptrace.signames import signalName, SIGNAMES
from signal import SIGTRAP, SIGALRM, SIGABRT, SIGSEGV, SIGCHLD, SIGWINCH, SIGFPE, SIGBUS, SIGTERM, SIGPIPE, signal, alarm
from errno import ESRCH, EPERM
from ptrace.cpu_info import CPU_POWERPC
from ptrace.debugger import ChildError

from time import sleep

from Event import Exit, Abort, Timeout, Crash, Signal, Call, specs, hash_events

from ELF import ELF
from Run import Launch
from MemoryMap import MemoryMaps

class Process(Application):
    def __init__(self, program, envs, no_stdout = False):

        Application.__init__(self)  # no effect

        self.program = str(program)
        self.name = self.program.split("/")[-1]
        #self.outdir = str(outdir)
        self.no_stdout = no_stdout
        self.envs = envs

        self.process = None
        self.pid = None
        self.mm = None
        self.timeouts = 0
        self.max_timeouts = 10

        # Parse ELF
        self.elf = ELF(self.program)
        self.modules = dict()

        self.last_signal = {}
        self.last_call = None
        self.crashed = False
        self.events = []

        self.binfo = dict()

        #self.followterms = []

    def setBreakpoints(self, elf):
      for func_name in elf.GetFunctions():
        if func_name in specs:
          #print func_name, hex(elf.FindFuncInPlt(func_name))
          addr = elf.FindFuncInPlt(func_name)
          self.binfo[addr] = elf.GetModname(),func_name
          self.breakpoint(addr)

    def findBreakpointInfo(self, addr):
      if addr in self.binfo:
        return self.binfo[addr]
      else:
        return None, None


    def createEvents(self, signal):

        # Hit breakpoint?
        if signal.signum == SIGTRAP:
            ip = self.process.getInstrPointer()
            if not CPU_POWERPC:
                # Go before "INT 3" instruction
                ip -= 1
            breakpoint = self.process.findBreakpoint(ip)
            #print "breakpoint @",hex(ip)
            
            if breakpoint:
                module, name = self.findBreakpointInfo(breakpoint.address)
                #print module, name, hex(ip)

                if ip == self.elf.GetEntrypoint():
                  breakpoint.desinstall(set_ip=True)

                  #if self.mm is None:
                  self.mm  = MemoryMaps(self.program, self.pid)
                  #self.setBreakpoints(self.elf)

                  #print self.mm

                  for (range, mod, atts) in self.mm.items():
                     if "/" in mod and 'x' in atts and not ("libc-" in mod):
                  
                        if mod == self.elf.path:
                           base = 0
                        else:
                           base = range[0]
 
                        if not (mod in self.modules):
                          self.modules[mod] = ELF(mod, base)

                        self.setBreakpoints(self.modules[mod])
            
                  return []

                elif name is None:
                  #print "unhoking return address"
                  #last_call = self.events[-1]
                  assert(self.last_call <> None)
                  #print breakpoint.address, self.last_call.GetReturnAddr()

                  breakpoint.desinstall(set_ip=True)
                  if (breakpoint.address == self.last_call.GetReturnAddr()):
                    self.last_call.DetectReturnValue(self.process)
                  else:
                    pass # FIXME: Why this could happen? setjmp/longjmp?

                  return []

                else:
                  call = Call(name, module) 
                  self.mm.update()
                  call.DetectParams(self.process, self.mm)
                  self.last_call = call
                  #print "hooking return address"
                  self.breakpoint(call.GetReturnAddr())

                  breakpoint.desinstall(set_ip=True)
                  self.process.singleStep()
                  self.breakpoint(breakpoint.address)

                  return [call]

        elif signal.signum == SIGABRT:
          self.crashed = True
          return [Signal("SIGABRT",self.process, self.mm), Abort(self.process, self.mm)]

        elif signal.signum == SIGSEGV:
          self.crashed = True
          self.mm  = MemoryMaps(self.program, self.pid)
          return [Signal("SIGSEGV", self.process, self.mm), Crash(self.process, self.mm)]

        elif signal.signum == SIGFPE:
          self.crashed = True
          self.mm  = MemoryMaps(self.program, self.pid)
          return [Signal("SIGFPE", self.process, self.mm), Crash(self.process, self.mm)]

        elif signal.signum == SIGBUS:
          self.crashed = True
          self.mm  = MemoryMaps(self.program, self.pid)
          return [Signal("SIGBUS", self.process, self.mm), Crash(self.process, self.mm)]

        elif signal.signum == SIGCHLD:
          self.crashed = True
          self.mm  = MemoryMaps(self.program, self.pid)
          return [Signal("SIGCHLD", self.process, self.pid), Crash(self.process, self.mm)]

        elif signal.signum == SIGTERM: # killed by the kernel?
          self.crashed = True
          return []

        # Harmless signals
        elif signal.signum == SIGPIPE:
          return [] # User generated, ignore.

        # Harmless signals
        elif signal.signum == SIGWINCH:
          return [] # User generated, ignore.

        else:
          print "I don't know what to do with this signal:", str(signal)
          assert(False)

        return []


    def createProcess(self, cmd, envs, no_stdout):

        self.pid = Launch(cmd, no_stdout, envs)
        #self.ofiles = list(files)
        is_attached = True

        try:
            return self.debugger.addProcess(self.pid, is_attached=is_attached)
        except (ProcessExit, PtraceError), err:
            if isinstance(err, PtraceError) \
            and err.errno == EPERM:
                error("ERROR: You are not allowed to trace process %s (permission denied or process already traced)" % self.pid)
            else:
                error("ERROR: Process can no be attached! %s" % err)
        return None

    def destroyProcess(self, signum, frame):
        assert(self.process is not None)
        print signum
        print frame

        #self.debugger.deleteProcess(self.process)
        #self.process.(SIGUSR2)
        #print "end!"
        #self.process.detach()


    def _continueProcess(self, process, signum=None):
        #print "begin _cont", self.last_signal
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
        #print "begin cont", signum

        for process in self.debugger:
            process.syscall_state.clear()
            if process == self.process:
                self._continueProcess(process, signum)
            else:
                self._continueProcess(process)

        #print "midle cont"
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
        timeout = 100
        alarm(timeout)

        # Create new process
        try:
            self.process = self.createProcess(cmd, self.envs, self.no_stdout)
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
        self.breakpoint(self.elf.GetEntrypoint())

        try:
          while True:
            #self.cont()
           
            if not self.debugger or self.crashed:
                # There is no more process: quit
                return
            else:
              self.cont()

          #alarm(0)
        except PtraceError:
          #print "deb:",self.debugger, "crash:", self.crashed
          alarm(0)
          return        

        except ProcessExit, event:
          alarm(0)
          self.events.append(Exit(event.exitcode))
          return

        except OSError:
          self.events.append(Timeout(timeout))
          self.timeouts += 1
          return

        except IOError:
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
        #print self.pid

        #if self.crashed:
        #  print "we should terminate.."
        #sleep(3)

        if self.process is None:
          return None

        self.process.terminate()
        self.process.detach()
        #print "terminated!"

        self.process = None
        return self.events


    def timeouted(self):
        return self.timeouts >= self.max_timeouts
