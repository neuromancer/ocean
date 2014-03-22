import os

from Input import Arg, File

def GetDir(filename):
  dirf = filename.replace(".tar.bz2","")

  #os.system("tar -xf "+ filename)
  #os.system("rm -f -R "+dirf)
  return dirf


def GetCmd(s):
  
  if os.path.exists("path.txt"):
    f = open("path.txt")
    x = f.readline()
    return x.replace("\n","").strip(" ")
  else: 
    return s

def GetArg(n, conc):
  
  # filename = "argv_"+str(n)+".symb"
  # data = open(filename).read()
  # x = Arg(n, data)

  if conc:
    filename = "cargv_"+str(n)+".symb"
    data = open(filename).read()
    x = Arg(n, data)
    x.SetConcrete()
  else:
    filename = "argv_"+str(n)+".symb"
    data = open(filename).read()
    x = Arg(n, data)
    x.SetSymbolic()

  return x


def GetArgs():
  #i = 1
  r = []

  for _,_,files in os.walk('.'):
    for f in files:
      #print f
      for i in range(10):
        #print str(i), f

        if ("cargv_"+str(i)) in f:
          x = GetArg(i, True)
          if x.IsValid():
            r.append(x)

          break

        elif ("argv_"+str(i)) in f:
          x = GetArg(i, False)
          if x.IsValid():
            r.append(x)

          break

  r.sort()
  #print r
  for i in range(len(r)):
    if r[i].i <> i+1:
      r = r[0:i]
      break

  #print r
  return r

def GetFile(filename, source):
  #size = int(os.path.getsize(source))
  data = open(source).read()
  return File(filename, data)

def GetFiles():

  r = []
  stdinf = "file___dev__stdin.symb"

  for dir,_,files in os.walk('.'):
    if dir == '.':
      for f in files:
        if (stdinf == f):
          r.append(GetFile("/dev/stdin",stdinf))
        elif ("file_" in f):
          filename = f.split(".symb")[0]
          #filename = f.replace(".symb","")
          filename = filename.split("file_")[1]
          filename = filename.replace(".__", "")
          x = GetFile(filename,f)
          if x.IsValid():
            r.append(x)

  return r

