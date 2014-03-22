import sys
import csv

import Event

events = []

with open(sys.argv[1]) as csvfile:
  reader = csv.reader(csvfile)

  for row in reader:
    for raw_event in row:
      if "[" in raw_event and "]" in raw_event:
        events.append(Event.GetEvent(raw_event))

for event in events:
  print event.GetVector()

