# -- coding: utf-8 --

import os

from ptrace.debugger.child import createChild
from os import dup2, close, open as fopen, O_RDONLY
from sys import stdin


def Launch(cmd, no_stdout, env):

  #cmd = ["/usr/bin/timeout", "-k", "1", "3"]+cmd
  #print cmd
  if cmd[-1][0] == "<":
    filename = cmd[-1].replace("< ", "")

    try:
      close(3)
    except OSError:
      pass

      desc = fopen(filename,O_RDONLY)
      dup2(desc, stdin.fileno())
      #close(desc)

    cmd = cmd[:-1]

  #print "cmd:", cmd
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
