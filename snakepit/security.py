from functools import wraps
from flask import g, session, abort
import bcrypt

def hash_pw(password):
    return bcrypt.hashpw(str(password), bcrypt.gensalt())

def test_pw(password, hashed):
    return bcrypt.hashpw(str(password), str(hashed)) == hashed

class Authenticator(object):

    def __init__(self, connector):
        self.connect = connector

    def get_current_user_roles(self):
        if not session["user"]:
            print "No user variable on the session"
            return set(["anon"])
        with self.connect() as store:
            u = store.fetch_user(**session["user"])
            if not u:
                print "No user found"
                session["user"] = None
                return set(["anon"])
            roles = set(str(role.name) for role in u.roles)
            print "Found:", roles
            return roles

    def requires_roles(self, *roles):
        roles = set(roles)
        def wrapper(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not self.get_current_user_roles() & roles:
                    return abort(403)
                return f(*args, **kwargs)
            return wrapped
        return wrapper

