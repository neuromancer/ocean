"""
This file is part of ocean.

SEA is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SEA is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SEA. If not, see <http://www.gnu.org/licenses/>.

Copyright 2014 by neuromancer
"""

import random
import Input

random.seed(0)

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
    assert(0)
  def GetData(self):
    return None
  def GetDelta(self):
    assert(0)

class SurpriceMutator(Mutator):

  max_expansion = 10000

  def __iter__(self):
    return self

  def next(self):

    input = self.input.copy()

    m = random.sample(["s","e","se"],1)[0]

    if "s" in m:
      # single byte mutation
      i = random.randrange(self.input_len)
      m = self.array[random.randrange(self.array_len)]
      input.data = input.data[:i] + m + input.data[i+1:]

    if "e" in m:
      # expansion mutation
      i = random.randrange(self.input_len)
      j = random.randrange(self.max_expansion)
      m = self.array[random.randrange(self.array_len)]

      #print self.array[rand]
      input.data = input.data[:i] + m*j + input.data[i+1:]

    return input

  def GetInput(self):
    return self.input.copy()

  def GetDelta(self):
    return None

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


class NullMutator(Mutator):

  def __iter__(self):
    return self

  def next(self):

    input = self.input.copy()
    return input

  def GetInput(self):
    return self.input.copy()

  def GetDelta(self):
    return None


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

    delta = dict()

    delta["aoffset"] = self.i
    delta["roffset"] = (float(self.i) / self.input_len) * 100
    delta["mtype"] = "."

    delta["byte"] = ord(self.array[self.array_i-1])

    delta["iname"] = self.input.GetName()
    delta["itype"] = self.input.GetType()

    return delta

class BruteForceExpander(Mutator):

  array_i = 0
  new_size = 300

  def __iter__(self):
    return self

  def next(self):

    i = self.i
    input = self.input.copy()
    #print self.array[rand]
    input.data = input.data[:i] + self.array[self.array_i]*self.new_size + input.data[i+1:]

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

    delta = dict()

    delta["aoffset"] = self.i
    delta["roffset"] = (float(self.i) / self.input_len) * 100
    delta["mtype"] = "+"+str(self.new_size)

    delta["byte"] = ord(self.array[self.array_i-1])

    delta["iname"] = self.input.GetName()
    delta["itype"] = self.input.GetType()

    return delta

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
    delta = None

    for j, m in enumerate(self.arg_mutators + self.file_mutators):
      if self.i == j and mutate:
         try:
           input = m.next()
           data = input.PrepareData()
           delta = m.GetDelta()
           #delta = input.GetType(), i, v

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


class RandomInputMutator:
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
    delta = None
    self.i = random.randrange(self.inputs_len)

    for j, m in enumerate(self.arg_mutators + self.file_mutators):
      if self.i == j:
        input = m.next()
        data = input.PrepareData()
        delta = m.GetDelta()

      else:
        input = m.GetInput()
        data = input.PrepareData()

      if data:
        r.append(data)

    return delta, r

