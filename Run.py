# -- coding: utf-8 --

from ptrace.debugger.child import createChild

def Launch(cmd, no_stdout, env):
  return createChild(cmd, no_stdout, env)


#class Runner:
#    def __init__(self, cmd, timeout):
#        #threading.Thread.__init__(self)
#
#        self.cmd = cmd
#        self.timeout = timeout
#
#    def Run(self):
#        #print self.cmd
#        self.p = subprocess.call(self.cmd, shell=False)
#        #self.p.wait()
#        #self.join(self.timeout)
#
#        #if self.is_alive():
#            #print "terminate: ", self.p.pid
#            #self.p.kill()
#            #self.join()
#            #return True
#        return True
