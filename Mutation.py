import random

import Input

class Mutator:
  def Mutate(self):
    pass

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
