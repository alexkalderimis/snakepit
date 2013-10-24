from nose.tools import *

import snakepit
from snakepit.schema import Base

CONFIG = snakepit.config.Config()
USER = {"name": "test user", "email": "foo@bar.com", "password": "foo"}

def select_keys(d, keys):
    return dict((k, v) for k, v in d.iteritems() if k in keys)

class StoreFixture(object):

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

class TestStore(StoreFixture):

    def test_1(self):
        data_store = snakepit.data.Store(CONFIG)

    def test_2(self):
        eq_(0, len(self.store.users()))

    def test_3(self):
        self.store.add_user(USER)
        eq_(1, len(self.store.users()))

class TestStoreWithUser(StoreFixture):

    def setup(self):
        super(TestStoreWithUser, self).setup()
        self.user = self.store.add_user(USER)

    def test_1(self):
        u = self.store.fetch_user(name = USER["name"])
        eq_(USER["name"], u.name)
        eq_(0, len(u.histories))
        eq_(u, self.user)

    def test_2(self):
        tragic_tale = "the tragic tale of the test user and his tribulations"
        self.user.new_history(tragic_tale)
        eq_([tragic_tale], [h.name for h in self.user.histories])

