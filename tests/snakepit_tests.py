from nose.tools import *

import snakepit
from snakepit.schema import Base

CONFIG = snakepit.config.Config()
USER = {"name": "test user", "email": "foo@bar.com", "password": "foo"}

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
        self.store.close()

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

    def test_user_in_eqs_user_out(self):
        u = self.store.fetch_user(name = USER["name"])
        eq_(USER["name"], u.name)
        eq_(USER["email"], u.email)
        eq_(0, len(u.histories))
        eq_(u, self.user)

    def test_can_add_history(self):
        tragic_tale = "the tragic tale of the test user and his tribulations"
        self.user.new_history(tragic_tale)
        eq_([tragic_tale], [h.name for h in self.user.histories])

class TestStoreWithHistories(StoreFixture):

    def setup(self):
        super(TestStoreWithHistories, self).setup()
        self.user = self.store.add_user(USER)
        (_, h, _) = (self.user.new_history(t) for t in ["hist1", "hist2", "hist3"])

        h.append_step("text/plain", "my search string")
        h.append_step("application/intermine-path-query",
                {"select":["Gene.id"],"where":{"id":[1,2,3]}})
        h.append_step("application/intermine-list", {"name": "my-list"})

    def test_histories_have_ids(self):
        ok_(all(h.id for h in self.user.histories))

    def test_can_get_history(self):
        h = self.user.histories[0]
        eq_("hist1", h.name)
        eq_([], h.steps)

    def test_can_add_step(self):
        h = self.user.histories[1]
        eq_(3, len(h.steps))

    def test_steps_come_in_order(self):
        h = self.user.histories[1]

        eq_("my search string", h.steps[0].data)
        eq_([1,2,3], h.steps[1].data["where"]["id"])

    def test_steps_know_where_they_come_from(self):
        h = self.user.histories[1]

        eq_(None, h.steps[0].previous_step)
        eq_(h.steps[0], h.steps[1].previous_step)

    def test_steps_know_where_they_go_to(self):
        h = self.user.histories[1]
        eq_([h.steps[1]], h.steps[0].next_steps)

    def test_can_fork_history(self):
        h = self.user.histories[1]
        forked = self.store.fork_history({"id": h.id}, 2)
        eq_(2, len(forked.steps))
        eq_(h.user, forked.user)
        eq_(4, len(self.user.histories))
        eq_(["text/plain", "application/intermine-path-query"], [s.mimetype for s in forked.steps])
        forked.append_step("application/csv", "Gene 1,Value 1\nGene 2,Value 2")
        eq_(3, len(forked.steps))
        eq_(h.steps[1].next_steps, [h.steps[-1], forked.steps[-1]])
        assert_false(h.steps[-1] in forked.steps)
        assert_false(forked.steps[-1] in h.steps)


