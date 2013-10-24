from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import User, History

class Store(object):

    def __init__(self, config):
        self.__engine__ = create_engine(config['DB_URL'])
        Session = sessionmaker(bind = self.__engine__)
        self.session = Session()

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

