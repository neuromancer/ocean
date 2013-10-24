import signal

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm
