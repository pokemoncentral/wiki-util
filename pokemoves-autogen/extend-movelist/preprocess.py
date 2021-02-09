"""Functions to convert data to its string representation."""

# from functools import partial

def map_dict(f, d):
    """Map over a dictionary."""
    return { k: f(v) for k, v in d.items() }

def _level_mapper(l):
    assert(len(l) == 1)
    return ", ".join(list(map(str, l[0])))

def level(data):
    return map_dict(_level_mapper, data)

def tm(data):
    return map_dict(lambda _: "yes", data)

preprocessers = {
    "level": level,
    "tm": tm
}

def preprocess(data):
    for k, v in data.items():
        if k in preprocessers:
            data[k] = preprocessers[k](v)
    return data
