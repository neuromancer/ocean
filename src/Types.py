"""
   Copyright (c) 2013 neuromancer
   All rights reserved.
   
   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:
   1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
   3. The name of the author may not be used to endorse or promote products
      derived from this software without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
   IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
   OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
   IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
   NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import copy

class Type:
  def __init__(self, name, size, index):
    self.name = str(name)
    self.size_in_bytes = size 
    self.index = index
    
  def __str__(self):
    
    r = str(self.name)
    
    if (self.index <> None):
      r = r +"("+str(self.index)+")"
    
    return r
    
  def copy(self):
    return copy.copy(self)
       
ptypes = [Type("Data32", None), 
          Type("Num32", None) , 
          Type("Ptr32", None) , # Generic pointer
          Type("SPtr32", None), # Stack pointer
          Type("HPtr32", None), # Heap pointer
          Type("NPtr32", None), # NULL pointer
          Type("DPtr32", None), # Dangling pointer
          Type("GPtr32", None), # Global pointer
          Type("Bot32", None) ]


