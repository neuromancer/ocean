import os

from Input import Arg, File

def GetCmd(s):
  
  if os.path.exists("path.txt"):
    f = open("path.txt")
    x = f.readline()
    return x.replace("\n","")  
  else: 
    return s

def GetArg(n):
  
  filename = "argv_"+str(n)+".symb" 
  data = open(filename).read()
  return Arg(n, data)

def GetArgs():
  #i = 1
  r = []

  for _,_,files in os.walk('.'):
    for f in files:
      #print f
      for i in range(10):
        #print "argv_"+str(i)
        if ("argv_"+str(i)) in f:
          x = GetArg(i)
          if x.IsValid(): 
            r.append(x)
          #else:
          #  r.sort()
          #  return r
          break

  r.sort()
  for i in range(len(r)):
    if r[i].i <> i+1:
      r = r[0:i]
      break

  return r

def GetFile(filename, source):
  #size = int(os.path.getsize(source))
  data = open(source).read()
  return File(filename, data)

def GetFiles():

  r = []
  stdinf = "file___dev__stdin.symb"
  os
  for _,_,files in os.walk('.'):
    for f in files:
      if (stdinf == f):
        r.append(GetFile("/dev/stdin",stdinf))
      elif ("file_" in f):
        filename = f.replace(".symb","")
        filename = filename.replace("file_","")        
        filename = filename.replace(".__", "")
        x = GetFile(filename,f) 
        if x.IsValid():
          r.append(x)

  return r

