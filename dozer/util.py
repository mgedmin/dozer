try:
    string_types = (str, unicode)
except NameError:
    # Python 3.x
    string_types = str


def asbool(obj):
    # Copied from paste.util.converters
    # (c) 2005 Ian Bicking and contributors; written for Paste
    # (http://pythonpaste.org).  Licensed under the MIT license:
    # https://www.opensource.org/licenses/mit-license.php
    if isinstance(obj, string_types):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError("String is not true/false: %r" % obj)
    return bool(obj)


def monotonicity(objs):
    # Monotonicity is a measurement of value increment over time
    # Large monotonicity indicates that number of objects
    # has been increased for a while, where leakage is likely to happen

    inc_cnt = 0.0
    dec_cnt = 1.0
    for i in range(len(objs) - 1):
        if objs[i+1] > objs[i]:
            inc_cnt += 1
        else:
            dec_cnt += 1
    return inc_cnt / (inc_cnt + dec_cnt)


def sort_dict_by_val(d, sort_key, reversed=False):
    # Sort a dictionary on its key
    return sorted(d.items(), key=lambda x: sort_key(x[1]), reverse=reversed)
