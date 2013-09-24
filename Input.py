class Input:
  def __init__(self):
    pass
  def copy(self):
    assert(False)

class Arg(Input):
  def __init__(self, i, data):
    self.i = i
    
    self.data = str(data)
    if ("\0" in data):
      self.data = self.data.split("\0")[0]

    self.size = len(data)

  def GetData(self):
    return str(self.data)
  
  def PrepareData(self):
    #return "\\\""+self.GetData()+"\\\""
    return "\""+self.GetData()+"\""

  def IsValid(self):
    return self.size > 0

  def __cmp__(self, arg):
    return cmp(self.i, arg.i)

  def copy(self):
    return Arg(self.i, self.data)

class File(Input):
  def __init__(self, filename, data):
    self.filename = str(filename)
    self.data = str(data)
    self.size = len(data)

  def GetData(self):
    return str(self.data)

  def PrepareData(self):
    if self.filename == "/dev/stdin":
      with open("Stdin", 'w') as f:
        f.write(self.data)

      return "< Stdin"
    else:
      with open(self.filename, 'w') as f:
        f.write(self.data)

      return ""

  def IsValid(self):
    return True

  def copy(self):
    return File(self.filename, self.data)    
