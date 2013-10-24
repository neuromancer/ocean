import random

import Input

class Mutator:
  def __init__(self, input):
    self.i = 0
    self.input = input.copy()
    self.input_len = len(input)

    if   isinstance(input, Input.Arg):
      self.array = map(chr, range(1, 256))
    elif isinstance(input, Input.File):
      self.array = map(chr, range(0, 256))

    self.array_len = len(self.array)

  #def GetDelta(self):

  def Mutate(self):
    pass
  def GetData(self):
    return None
  def GetDelta(self):
    pass

"""
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


class CompleteMutator(Mutator):

  def __init__(self, input):
    Mutator.__init__(self, input)

    self.array = filter(lambda b: b <> "'", self.array)
    self.size -= 1

    #input = self.input.copy()
    ilen = input.GetSize()
    self.input.data = ""
    for i in range(ilen):
      rand = random.randint(0,self.size-1)
      self.input.data += self.array[rand]

    #self.input = input

  def Mutate(self):
    i = self.i
    rand = random.randint(0,self.size-1)
    input = self.input.copy()
    #print self.array[rand]
    input.data = input.data[:i] + self.array[rand] + input.data[i+1:]
    #print input.data
    self.i = (i + 1) % len(input.data)
    return input

  def GetInput(self):
    return self.input.copy()
"""

class BruteForceMutator(Mutator):

  array_i = 0

  def __iter__(self):
    return self

  def next(self):

    i = self.i
    input = self.input.copy()
    #print self.array[rand]
    input.data = input.data[:i] + self.array[self.array_i] + input.data[i+1:]

    if self.array_i == self.array_len-1:
      self.array_i = 0

      if i == self.input_len-1:
        raise StopIteration
      else:
        self.i = self.i + 1

    else:
      self.array_i = self.array_i + 1

    return input

  def GetInput(self):
    return self.input.copy()

  def GetDelta(self):
    rel = (float(self.i) / self.input_len) * 100
    return rel, ord(self.array[self.array_i-1])

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

    self.inputs = self.arg_mutators + self.file_mutators
    self.inputs_len = len(self.inputs)
  #def __mutate__(self, j,

  def __iter__(self):
    return self

  def next(self, mutate = True):
    r = []

    for j, m in enumerate(self.arg_mutators + self.file_mutators):
      if self.i == j and mutate:
         try:
           input = m.next()
           data = input.PrepareData()
           i,v = m.GetDelta()
           delta = input.GetType(), i, v

         except StopIteration:
           self.i = self.i + 1

           if self.i == self.inputs_len:
             raise StopIteration

           return self.next()

      else:
        input = m.GetInput()
        data = input.PrepareData()

      if data:
        r.append(data)

    return delta, r

  #def GetDelta(self):
  #
  #  mutator = self.inputs[self.i]
  #  input = mutator.GetInput()
  #
  #  offset, val = mutator.GetDelta()
  #  return [input.GetName(), offset, val]:

    #f = lambda m: m.GetInput().PrepareData()

    #args = GetArgs()
    #files = GetFiles()
    #mutator = RandomMutator(args[1])

    #for i in range(0):
    #  mutator.Mutate()

    #args[0] = mutator.Mutate()

    #return " ".join(map(f,self.arg_mutators)) + " " + "".join(map(f,self.file_mutators))
    #+ " > /dev/null 2> /dev/null\""

