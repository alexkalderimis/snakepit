from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import User, History

def select_keys(d, keys):
    return dict((k, v) for k, v in d.iteritems() if v is not None and k in keys)

class Store(object):

    def __init__(self, config):
        self.__engine__ = create_engine(config['DB_URL'])
        self._session_factory = sessionmaker(bind = self.__engine__)
        self.session = self._session_factory()

    def users(self):
        return self.session.query(User).all()

    def add_user(self, data):
        u = User(**data)
        self.session.add(u)
        return u

    def fetch_user(self, **args):
        if args["name"] is None and args["id"] is None:
            raise ArgumentError("name or id required")
        return self.session.query(User).filter_by(**args).one()

    def fork_history(self, history, index):
        """
        Make a new history, retaining the first n steps from the old one.
        """
        h = self.session.query(History).filter_by(**select_keys(history, ["id", "name"])).one()
        hh = h.user.new_history(h.name)
        hh.steps = h.steps[:index]
        return hh

    def close(self):
        if self.session is not None: self.session.close()

    def __enter__(self):
        if self.session is not None: self.session.close()
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

