from src.Event    import Call, Crash, Abort, Exit, Signal, Vulnerability
from Analysis import FindModule 

def detect_vulnerabilities(preevents, events, process, mm):

  r = []

  for (i, event) in enumerate(events):  
    r.append(detect_vulnerability(preevents, event, process, mm))

  return filter(lambda e: e is not None, r)

def detect_vulnerability(preevents, event, process, mm):
 
    if isinstance(event, Call):

      (name, args) = event.GetTypedName()
      if name == "system" or name == "popen":
       pass    

    elif isinstance(event, Abort):

      if len(event.bt) > 0 and len(preevents) > 0:

        if not (str(preevents[-1]) in ["free", "malloc", "realloc"]):
          return None 

        for (typ, val) in event.bt:
           module = FindModule(val, mm)
           if module == "[vdso]":
             pass
           elif "libc-" in module:
             return Vulnerability("MemoryCorruption")
           else:
             return None 

    elif isinstance(event, Crash):

      if str(event.fp_type[0]) == "DPtr32" and str(event.eip_type[0]) == "DPtr32":
        return Vulnerability("StackCorruption")

      for (typ,val) in event.bt:        
        if str(typ) == "DPtr32":
          return Vulnerability("StackCorruption")

    elif isinstance(event, Signal):
      pass

    return None



