from nose.tools import *
import snakepit
import snakepit.webapp as web

user = {"name": "Test User", "password": "passw0rd", "email": "user@foo.com"}

class TestWebapp(object):

    CONF = snakepit.config.Config("TEST")

    @classmethod
    def setup_class(cls):
        with snakepit.data.Store(cls.CONF) as store:
            store.create_db()
            u = store.add_user(user)

    @classmethod
    def teardown_class(cls):
        snakepit.data.Store(cls.CONF).clear_db()

    def setup(self):
        app = web.app
        print(TestWebapp.CONF)
        app.config.update(TestWebapp.CONF)
        app.config['TESTING'] = True
        self.app = web.app.test_client()

    def teardown(self):
        pass

    def login(self, username, password):
        return self.app.post('/login', data=dict(
                username=username,
                password=password
            ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_welcome(self):
        rv = self.app.get("/")
        assert_true("Hello World" in rv.data)

    def test_login_logout(self):
        rv = self.login('Test User', 'passw0rd')
        print repr(rv.data)
        assert 'histories' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('Test Userx', 'passw0rd')
        assert 'Invalid username' in rv.data
        rv = self.login('Test User', 'passw0rdx')
        assert 'Invalid password' in rv.data
