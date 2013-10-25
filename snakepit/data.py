from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import User, History, Base, Role

def select_keys(d, keys):
    return dict((k, v) for k, v in d.iteritems() if v is not None and k in keys)

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
        u = User(**data)
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
        self.close()
        return False

