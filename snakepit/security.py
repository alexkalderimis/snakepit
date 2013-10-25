from functools import wraps
from flask import g, session
import bcrypt

def hash_pw(password):
    return bcrypt.hashpw(str(password), bcrypt.gensalt())

def test_pw(password, hashed):
    return bcrypt.hashpw(str(password), str(hashed)) == hashed

class Authenticator(object):

    def __init__(self, connector, on_fail):
        self.connect = connector
        self.on_fail = on_fail

    def get_current_user_roles(self):
        if not "user" in session:
            return set(["anon"])
        with self.connect() as store:
            u = store.fetch_user(**session["user"])
            if not u:
                session["user"] = None
                return set(["anon"])
            roles = set(str(role.name) for role in u.roles)
            return roles

    def requires_roles(self, *roles):
        roles = set(roles)
        def wrapper(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not self.get_current_user_roles() & roles:
                    return self.on_fail()
                return f(*args, **kwargs)
            return wrapped
        return wrapper

