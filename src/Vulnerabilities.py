from src.Event    import Call, Crash, Abort, Exit, Signal, specs


def detect_vulnerability(events, process):

  r = None
  for event in events:
    r = _detect_vulnerability(event, process)
    
    if r <> None:
      return r

  return r


def _detect_vulnerability(event, process):

    mm =     
   
    if isinstance(event, Call):

      #print event.name, event.param_types, event.ret, event.retaddr, event.retvalue
      (name, args) = event.GetTypedName()

      #r.add((name+":ret_addr",str(args[0])))
      r.append((name+":ret_val",str(args[1])))

      for (index, arg) in enumerate(args[2:]):
        r.append((name+":"+str(index),str(arg)))
        #print r
    elif isinstance(event, Abort):
      (name, fields) = event.GetTypedName()
      r.append((name+":eip",str(fields[0])))
    
    elif isinstance(event, Exit):
      (name, fields) = event.GetTypedName()
      r.append((name,str(())))
    
    elif isinstance(event, Crash):

      self.bt =  process.getBacktrace()
      for frame in self.bt:
        r_type = RefinePType(Type("Ptr32",4), frame.ip, process, mm)
        if str(r_type[0]) == "DPtr32":
          return Vulnerability("StackOverflow")

    elif isinstance(event, Signal):

    return None



