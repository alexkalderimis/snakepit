def select_keys(d, keys, mapping = None):
    if mapping is None: mapping = {}
    return dict((mapping.get(k, k), v) for k, v in d.iteritems() if v is not None and k in keys)

def unpack(d, keys):
    map(lambda k: d.get(k), keys)
