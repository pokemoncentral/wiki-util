import sys

count = 899
f = open(sys.argv[1], "r")
with open("/tmp/e.lua", "w") as o:
    for line in f:
        o.write(line.replace("nil", str(count)))
        if len(line) > 1 and line[1] == "[":
            prefix = line.split("]", 1)[0] + "]"
        else:
            prefix = line.split(" ", 1)[0]
        o.write("t[" + str(count) + "] = " + prefix + "\n")
        count += 1
