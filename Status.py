
class TimeoutEx(Exception):
    pass

def alarm_handler(signum, frame):
    print signum
    print frame
    raise TimeoutEx

#class CrashEx()
