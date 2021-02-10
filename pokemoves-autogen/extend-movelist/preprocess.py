"""Functions to convert data to its string representation."""

# from functools import partial

def map_dict(f, d):
    """Map over a dictionary."""
    return { k: f(v) for k, v in d.items() }

def __level_mapper(l):
    assert(len(l) == 1)
    return ", ".join(list(map(str, l[0])))

def level(data):
    return map_dict(__level_mapper, data)

def tm(data):
    return map_dict(lambda _: "yes", data)

def __breed_mapper(l):
    assert(len(l) == 1)
    return "".join(list(map(lambda x: "#" + str(x) + "#", l[0])))

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

def preprocess(data):
    for k, v in data.items():
        if k in preprocessers:
            data[k] = preprocessers[k](v)
    return data
