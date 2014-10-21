#!/usr/bin/python2

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

import sys

from src.ELF  import ELF, load_plt_calls
from src.Spec import specs


if __name__ == "__main__":
  inss = load_plt_calls(sys.argv[1])
  print sys.argv[1]+"\t",
  for ins in inss:
    if ins[1] in specs:
      print ins[1],

  #elf = ELF(sys.argv[1])
  #elf._load_sections()
  #elf._load_instructions()
  #print elf.raw_instructions


