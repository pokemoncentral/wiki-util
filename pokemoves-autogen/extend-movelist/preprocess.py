"""Functions to convert data to its string representation."""

# from functools import partial

def map_dict(f, d):
    """Map over a dictionary."""
    return { k: f(v) for k, v in d.items() }

def __level_key(v):
    if v == "Evo":
        return 1.5
    return float(v)

def __level_mapper(l):
    assert(len(l) == 1)
    return ", ".join(sorted(list(map(str, l[0])), key=__level_key))

def level(data):
    return map_dict(__level_mapper, data)

def tm(data):
    return map_dict(lambda _: "yes", data)

def __breed_mapper(l):
    assert(len(l) == 1)
    return "".join(list(map(lambda x: "#" + str(x).zfill(3) + "#", l[0])))

def breed(data):
    return map_dict(__breed_mapper, data)

def __tutor_mapper(l):
    return list(map(lambda b: "yes" if b else "no", l))

def tutor(data):
    # return map_dict(__tutor_mapper, data)
    return None

preprocessers = {
    "level": level,
    "tm": tm,
    "breed": breed,
    "tutor": tutor
}

def fix_lua_python_indices(data):
    """
    Increase initial keys by one to cope with differend indexing of Lua
    and python (1- and 0-based) because keys are ndexes.
    """
    if data is None:
        return None
    i = 0
    while i in data:
        i += 1
    while i > 0:
        data[i] = data[i - 1]
        i -= 1
    if 0 in data:
        del data[0]
    return data

def preprocess(data):
    for k, v in data.items():
        if k in preprocessers:
            data[k] = fix_lua_python_indices(preprocessers[k](v))
    return data
