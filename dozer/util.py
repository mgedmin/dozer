import base64
import binascii
import hmac

from webob import exc


def parse_basic_auth(basic_auth):
    """Normalize a basic_auth configuration value to (username, password).

    Accepts a (username, password) pair or a 'username:password' string
    (the form used in PasteDeploy configuration files).
    """
    if isinstance(basic_auth, str):
        username, sep, password = basic_auth.partition(':')
        if not sep:
            raise ValueError(
                "basic_auth must be a (username, password) pair or a "
                "'username:password' string")
        return (username, password)
    try:
        username, password = basic_auth
    except (TypeError, ValueError):
        raise ValueError(
            "basic_auth must be a (username, password) pair or a "
            "'username:password' string")
    return (username, password)


def check_basic_auth(authorization, credentials):
    """Check an HTTP Authorization header against some credentials.

    Returns True if the header carries valid HTTP Basic authentication
    data matching the given (username, password) pair.
    """
    if not authorization:
        return False
    try:
        scheme, token = authorization.split(None, 1)
    except ValueError:
        return False
    if scheme.lower() != 'basic':
        return False
    token += '=' * (-len(token) % 4)  # tolerate unpadded base64
    try:
        userpass = base64.b64decode(token, validate=True)
    except binascii.Error:
        return False
    username, sep, password = userpass.decode(
        'utf-8', 'replace').partition(':')
    if not sep:
        return False
    expected_user, expected_password = credentials
    return (hmac.compare_digest(username.encode('utf-8'),
                                expected_user.encode('utf-8'))
            and hmac.compare_digest(password.encode('utf-8'),
                                    expected_password.encode('utf-8')))


def unauthorized():
    """Build a 401 response that asks for HTTP Basic authentication."""
    return exc.HTTPUnauthorized(
        'Authentication required',
        headers=[('WWW-Authenticate', 'Basic realm="Dozer"')])


def asbool(obj):
    # Copied from paste.util.converters
    # (c) 2005 Ian Bicking and contributors; written for Paste
    # (http://pythonpaste.org).  Licensed under the MIT license:
    # https://www.opensource.org/licenses/mit-license.php
    if isinstance(obj, str):
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
