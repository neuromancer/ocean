
class TimeoutEx(Exception):
    pass

def alarm_handler(signum, frame):
    raise TimeoutEx

#class CrashEx()
