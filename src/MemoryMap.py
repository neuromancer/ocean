class MemoryMaps:
  def __init__(self, path, pid):
    self.path = str(path)
    self.pid  = pid
    self.update()

  def update(self):

    self.mm = dict()
    self.atts = dict()

    for line in open('/proc/'+str(self.pid)+'/maps'):
      line = line.replace("\n", "")
      #print line
      x = line.split(" ")

      mrange = x[0].split("-")
      mrange = map(lambda s: int(s, 16), mrange)
      #print tuple(mrange)

      self.mm[tuple(mrange)] = x[-1]
      self.atts[tuple(mrange)] = x[1]

  def isStackPtr(self, ptr):
    for (mrange,zone) in self.mm.items():
      if ptr >= mrange[0] and ptr < mrange[1]:
          return zone == "[stack]"
    return False

  def isHeapPtr(self, ptr):
    for (mrange,zone) in self.mm.items():
      if ptr >= mrange[0] and ptr < mrange[1]:
          return zone == "[heap]"
    return False

  def isLibPtr(self, ptr):
    for (mrange,zone) in self.mm.items():
      if ptr >= mrange[0] and ptr < mrange[1]:
          return "/lib/" in zone
    return False

  def isGlobalPtr(self, ptr):
    for (mrange,zone) in self.mm.items():
      if ptr >= mrange[0] and ptr < mrange[1]:
          return zone == self.path
    return False

  def isFilePtr(self, ptr):
    for (mrange,zone) in self.mm.items():
      if ptr >= mrange[0] and ptr < mrange[1]:
          return zone == ""
    return False

  def checkPtr(self, ptr, update=True):
    for (mrange,zone) in self.mm.items():
      if ptr >= mrange[0] and ptr < mrange[1]:
          return True

    if update:
      self.update()
    return self.checkPtr(ptr, update=False)

  def __str__(self):
    r = ""
    for (mrange,zone) in self.mm.items():
      r = r + hex(mrange[0])+" - "+hex(mrange[1])+" -> "+zone+"\n"
    return r

  def items(self):
    r = []
    for (x,y) in self.mm.items():
      r.append((x,y,self.atts[x]))

    return r


