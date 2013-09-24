import random

import Input

class Mutator:
  def __init__(self, input):
    self.i = 0
    self.input = input.copy()
    if   isinstance(input, Input.Arg):
      self.array = map(chr, range(1,256))
    elif isinstance(input, Input.File):
      self.array = map(chr, range(0,256))

    self.size = len(self.array)

  def Mutate(self):
    pass
  def GetData(self):
    return

class RandomMutator(Mutator):

  def Mutate(self):
    i = self.i
    rand = random.randint(0,self.size-1)
    input = self.input.copy()
    #print self.array[rand]
    input.data = input.data[:i] + self.array[rand] + input.data[i+1:]
    print input.data
    self.i = i + 1
    return input

  def GetInput(self):
    return self.input.copy()

class BruteForceMutator(Mutator):
  
  array_i = 0 
  def Mutate(self):
    i = self.i
    input = self.input.copy()
    #print self.array[rand]
    input.data = input.data[:i] + self.array[self.array_i] + input.data[i+1:]
    if (self.array_i == len(self.array)-1):
      self.array_i = 0
      self.i = self.i + 1
    else:
      self.array_i = self.array_i + 1
    return input

  def GetInput(self):
    return self.input.copy()


class InputMutator:
  def __init__(self, args, files, mutator):
    assert(args <> [] or files <> [])
    self.i = 0
    self.arg_mutators  = []
    self.file_mutators = []
    #self.inputs = list(inputs)

    for input in args:
      self.arg_mutators.append(mutator(input))
    for input in files:
      self.file_mutators.append(mutator(input))
  #def __mutate__(self, j,  

  def GetMutatedInput(self): 
    r = ""
    for j,m in enumerate(self.arg_mutators + self.file_mutators):
      if self.i == j:
         r = r + m.Mutate().PrepareData() + " "
      else:
         r = r + m.GetInput().PrepareData() + " "

    return r

    #f = lambda m: m.GetInput().PrepareData()

    #args = GetArgs()
    #files = GetFiles()
    #mutator = RandomMutator(args[1])

    #for i in range(0):
    #  mutator.Mutate()

    #args[0] = mutator.Mutate()

    return " ".join(map(f,self.arg_mutators)) + " " + "".join(map(f,self.file_mutators)) #+ " > /dev/null 2> /dev/null\""

