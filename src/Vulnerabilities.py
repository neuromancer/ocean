from src.Event    import Call, Crash, Abort, Exit, Signal, Vulnerability

def detect_vulnerabilities(events, process):

  r = map(lambda event: detect_vulnerability(event, process), events)
  return filter(lambda e: e is not None, r)

def detect_vulnerability(event, process):
 
    if isinstance(event, Call):

      (name, args) = event.GetTypedName()
      if name == "system" or name == "popen":
       pass    

    elif isinstance(event, Abort):
      for (typ,val) in event.bt:
        if val == 0xb7f3f980: #__fortify_fail address
          return Vulnerability("StackCorruption")

        if val == 0xb71be8ad: # crash inside cfree (free)
          return Vulnerability("HeapCorruption")



    elif isinstance(event, Crash):

      for (typ,val) in event.bt:
        if str(typ) == "DPtr32":
          return Vulnerability("StackOverflow")

    elif isinstance(event, Signal):
      pass

    return None



