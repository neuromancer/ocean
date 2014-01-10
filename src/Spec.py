import os

realpath = os.path.dirname(os.path.realpath(__file__))
datadir = "../data/"
f = open(realpath+"/"+datadir+"prototypes.conf")
specs = dict()

for raw_spec in f.readlines():
    raw_spec = raw_spec.replace("\n", "")
    raw_spec = raw_spec.replace(", ", ",")
    raw_spec = raw_spec.replace(" (", "(")
    raw_spec = raw_spec.replace("  ", " ")
    raw_spec = raw_spec.replace("  ", " ")
    if raw_spec <> "" and raw_spec[0] <> ";" and (not "SYS_" in raw_spec):
        x = raw_spec.split(" ")
        ret = x[0]
        x = x[1].split("(")
        name = x[0]
        param_types  = x[1].replace(");", "").split(",")
        specs[name] = [ret] + param_types

#print specs
