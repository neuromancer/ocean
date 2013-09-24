# -- coding: utf-8 --

import subprocess
import sys

class Runner:
    def __init__(self, cmd, timeout):
        #threading.Thread.__init__(self)
        
        self.cmd = cmd
        self.timeout = timeout

    def Run(self):
        print self.cmd
        self.p = subprocess.Popen(self.cmd)
        self.p.wait()
        #self.join(self.timeout)

        #if self.is_alive():
            #print "terminate: ", self.p.pid
            #self.p.kill()
            #self.join()
            #return True
        return True
