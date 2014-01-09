import pydot

from Event import isNull, isPtr

class CallGraph:

  def __init__(self, events):

    self.graph = pydot.Dot(graph_type='digraph')
    events = events[-100:]
    for event in events:
      #print repr(str(event))
      node = pydot.Node(str(event).replace(":", ""))
      self.graph.add_node(node)

    for (i, call0) in enumerate(events[:-1]):
      #print "call0:", str(call0)
      found = False
      for (typ0, par0) in call0.GetReturnValue():
        #print typ0, par0
        if isPtr(typ0) and not isNull(par0):

          for j in range(i+1,len(events)-1):
          #for call1 in events[i+1:-1]:

            call1 = events[j]

            #print "call1:", str(call1)
            for (typ1, par1) in call1.GetParameters():
              node0 = str(i)+" "+str(call0).split(":")[1]
              node1 = str(j)+" "+str(call1).split(":")[1]
              if (par0 == par1 and node0 <> node1):
                #print "Found!"
                self.graph.add_edge(pydot.Edge(node0, node1, label=par0))
                found = True

            if found:
              break

      found = False

      for (typ0, par0) in call0.GetParameters():
        if isPtr(typ0) and not isNull(par0):


          #for call1 in events[i+1:-1]:
          for j in range(i+1, len(events)-1):
            call1 = events[j]

            #print "call1:",str(call1)
            for (typ1, par1) in call1.GetParameters():
              node0 = str(i)+" "+str(call0).split(":")[1]
              node1 = str(j)+" "+str(call1).split(":")[1]

              if (par0 == par1 and node0 <> node1):
                #print "Found!"
                self.graph.add_edge(pydot.Edge(node0, node1, label=par0))
                found = True

            if found:
              break

  def WriteGraph(self, filename):
    self.graph.write_dot(filename)