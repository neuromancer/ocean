import random

import Input

class Mutator:
  def Mutate(self):
    pass
  def GetData(self):
    return

class RandomMutator(Mutator):

  def __init__(self, input):
    self.i = 0
    self.input = input.copy()
    print input, self.input
    if   isinstance(input, Input.Arg):
      self.array = map(chr, range(1,256))
    elif isinstance(input, Input.File):
      self.array = map(chr, range(0,256))

    self.size = len(self.array)

  def Mutate(self):
    i = self.i
    input = self.input.copy()
    input.data = input.data[:i] + self.array[random.randint(0,self.size-1)] + input.data[i+1:]
    self.i = i + 1
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
      
  def GetMutatedInput(self): 
    f = lambda m: m.GetInput().PrepareData()

    #args = GetArgs()
    #files = GetFiles()
    #mutator = RandomMutator(args[1])

    #for i in range(0):
    #  mutator.Mutate()

    #args[0] = mutator.Mutate()

    return " ".join(map(f,self.arg_mutators)) + " " + "".join(map(f,self.file_mutators)) #+ " > /dev/null 2> /dev/null\""

