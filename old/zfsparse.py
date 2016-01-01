import re
def units(m):
    num, u = float(m.group(1)), m.group(2)
    bytes = num * (1 << dict(K=10, M=20, G=30)[u])
    return str(bytes)

def formatGb(bytes):
    gb = int(bytes) / (1<<30)
    return "%.03f" % gb

def toGigabytes(line):
    return re.sub(r"([\d\.]+)([MGK])", lambda m: formatGb(units(m)), line)

def toBytes(line):
    return re.sub(r"([\d\.]+)([MGK])", units, line)
