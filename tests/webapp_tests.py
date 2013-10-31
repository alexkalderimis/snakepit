from nose.tools import *
import snakepit
import snakepit.webapp as web
import json
from operator import itemgetter

user = {"name": "Test User", "password": "passw0rd", "email": "user@foo.com"}
JSON = 'application/json'
credentials = (user['name'], user['password'])
accept_json = ('Accept', JSON)
accept_html = ("Accept", "text/html")
accept_any = ('Accept', '*/*')
json_content = ('Content-Type', JSON)

class Client(object):

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
        app.config.update(Client.CONF)
        app.config['TESTING'] = True
        self.app = web.app.test_client()

    def teardown(self):
        pass

    def api(self, meth, path, headers = None, **kwargs):
        f = self.app.get if meth == 'GET' else self.app.post
        hs = [] if headers is None else headers[:]
        hs.append(accept_json)
        rv = f(path, headers = hs, **kwargs)
        try:
            data = json.loads(rv.data)
        except ValueError:
            data = None
        return rv, data

    def login(self, username, password):
        return self.app.post('/login', data=dict(
                username=username,
                password=password
            ), headers = [("Accept", "text/html")])

    def register(self, username, password, confirm = None, email = None):
        """Helper to register a user"""
        if confirm is None:
            confirm = password
        if email is None:
            email = username + "@foo.com"
        return self.app.post("/register", data = {
            "username": username,
            "password": password,
            "confirmpassword": confirm,
            "email": email
            }, headers = [accept_html])

    def logout(self):
        return self.app.get('/logout',
                follow_redirects = True,
                headers          = [accept_json, accept_html])

class TestFrontDoor(Client):

    def test_welcome(self):
        rv = self.app.get("/")
        eq_(302, rv.status_code)
        eq_('http://localhost/histories', rv.headers['Location'])

    def test_login_logout(self):
        rv = self.login(*credentials)
        eq_(302, rv.status_code)
        eq_('http://localhost/histories', rv.headers['Location'])
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('Test Userx', 'passw0rd')
        assert 'Invalid username' in rv.data
        rv = self.login('Test User', 'passw0rdx')
        assert 'Invalid password' in rv.data

    def test_register(self):
        new_user = ("new user", "foo")

        rv = self.login(*new_user)
        assert 'Invalid username' in rv.data

        rv = self.register(*new_user)
        eq_(302, rv.status_code)
        eq_('http://localhost/histories', rv.headers['Location'])

        self.logout()

        rv = self.login(*new_user)
        eq_(302, rv.status_code)
        eq_('http://localhost/histories', rv.headers['Location'])


class TestData(Client):

    def setup(self):
        super(TestData, self).setup()
        self.login(*credentials)

    def teardown(self):
        self.logout()
        super(TestData, self).teardown()

    def test_histories(self):

        hist = {'histname': 'new history'}

        rv, jval = self.api('GET', '/histories')
        eq_(jval['histories'], [])

        rv, jval = self.api('POST', '/histories', data = hist)
        ok_(jval['history'])
        h_url = jval['history']

        rv, jval = self.api('GET', '/histories')
        eq_(1, len(jval['histories']))
        eq_([h_url], map(itemgetter('url'), jval['histories']))

        rv, jval = self.api('GET', h_url)
        eq_('new history', jval['name'])

    def test_steps(self):

        hist = {'histname': 'new history'}
        rv, jval0 = self.api('POST', '/histories', data = hist)

        h_url = jval0['history']
        rv, history = self.api('GET', h_url)

        eq_(0, len(history['steps']))

        data = json.dumps({
            "tool": "http://tools.intermine.org/keyword-search",
            "mimetype": "text/plain",
            "data": "my search string"
        })

        r, step = self.api('POST', h_url, data = data, content_type = JSON)

        eq_(201, r.status_code)
        s_url = r.headers['Location']

        rv, history = self.api('GET', h_url)

        eq_(1, len(history['steps']))
        ok_(s_url.endswith(history['steps'][0]['url']))

