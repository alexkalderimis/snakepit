from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import User, History, Base, Role, Client, Grant, BearerToken
from utils import select_keys

class Store(object):

    def __init__(self, config):
        self.__engine__ = create_engine(config['DB_URL'])
        self._session_factory = sessionmaker(bind = self.__engine__)
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = self._session_factory()
        return self._session

    def create_db(self):
        Base.metadata.create_all(self.__engine__)

    def clear_db(self):
        Base.metadata.drop_all(self.__engine__)

    def users(self):
        return self.session.query(User).all()

    def get_role(self, name):
        r = self.session.query(Role).filter_by(name = name).first()
        if r is None:
            r = Role(name = name)
            self.session.add(r)
        return r

    def add_user(self, data):
        u = User(**select_keys(data, ["name", "password", "email"]))
        r = self.get_role("user")
        u.roles.append(r)
        self.session.add(u)
        return u

    def fetch_user(self, **args):
        if args["name"] is None and args["id"] is None:
            raise ArgumentError("name or id required")
        return self.session.query(User).filter_by(**args).first()

    def fork_history(self, history, index):
        """
        Make a new history, retaining the first n steps from the old one.
        """
        h = self.session.query(History).filter_by(**select_keys(history, ["id", "name"])).one()
        hh = h.user.new_history(h.name)
        hh.steps = h.steps[:index]
        return hh

    def fetch_client(self, client):
        if "id" not in client:
            raise ArgumentError("id must be provided")
        constraint = select_keys(client, ["id"])

        return self.session.query(Client).filter_by(**constraint).first()

    def get_grant(self, client_id, code):
        return session.query(Grant).\
                       filter_by(client_id = client_id, code = code).\
                       first()

    def save_grant(self, user, client, code, redirect_uri, scopes, expires):
        grant = Grant(
            client = client,
            code = code,
            redirect_uri = redirect_uri,
            scopes = scopes,
            user = user,
            expires = expires)
        self.session.add(grant)
        return grant

    def get_token(self, contraint):
        return self.query(BearerToken).filter_by(**contraint).first()

    def add_token(self, client, user, attrs):
        toks = BearerToken.query.filter_by(client = client, user = user)
        self.session.delete(toks)
        to_store = select_keys(attrs, ["accept_token", "refresh_token", "token_type", "expires_in"])
        to_store.update(dict(
            scopes = token["scope"].split(),
            user = user,
            client = client))
        tok = BearerToken(**to_store)
        self.session.add(tok)
        return tok



    def close(self):
        if self._session is not None: self._session.close()
        self._session = None

    def __enter__(self):
        self.close() # Start with new session
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type or exc_val:
            self.session.rollback()
        else:
            self.session.commit()
        return False

