import subprocess
import threading

class Runner(threading.Thread):
    def __init__(self, cmd, timeout):
        #threading.Thread.__init__(self)
        self.cmd = map(lambda s: str(unicode(s)), cmd)
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
