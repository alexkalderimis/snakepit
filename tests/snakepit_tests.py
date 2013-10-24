from nose.tools import *

import snakepit
from snakepit.schema import Base

CONFIG = {"DB_URL": "postgresql://alex:alex@localhost:5432/snakepit-test"}
USER = {"name": "test user", "email": "foo@bar.com", "password": "foo"}

class TestStore(object):

    @classmethod
    def setup_class(cls):
        Base.metadata.create_all(snakepit.data.Store(CONFIG).__engine__)

    @classmethod
    def teardown_class(cls):
        try:
            Base.metadata.drop_all(snakepit.data.Store(CONFIG).__engine__)
        except Exception as e:
            print(e)

    def setup(self):
        self.store = snakepit.data.Store(CONFIG)

    def teardown(self):
        self.store.session.rollback()

    def test_1(self):
        data_store = snakepit.data.Store(CONFIG)

    def test_2(self):
        eq_(0, len(self.store.users()))

    def test_3(self):
        self.store.add_user(USER)
        eq_(1, len(self.store.users()))

    def test_4(self):
        self.store.add_user(USER)
        u = self.store.fetch_user(name = USER["name"])
        eq_(USER["name"], u.name)
        eq_(0, len(u.histories))

