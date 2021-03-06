from flask import Flask, g, flash, request, session, redirect, \
        make_response, url_for, abort, render_template, flash, json

from datetime import datetime, timedelta
import os.path as path
from flask_negotiate import consumes, produces
from flask_oauthlib.provider import OAuth2Provider
import logging

# snakepit code
from security import test_pw, Authenticator
from utils import select_keys
import config
import data

templates = path.realpath(path.join(path.dirname(__file__), "..", "templates"))

app = Flask('snakepit', template_folder = templates)
app.config.update(config.Config())

oauth = OAuth2Provider(app)

if not app.debug:
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler("snakepit.log", maxBytes = 10000000)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

class InputError(Exception):

    def __init__(self, message):
        super(Exception, self).__init__()
        self.message = message

def init_db():
    """Creates the database tables."""
    with app.app_context():
        get_datastore().create_db()

def get_datastore():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'datastore'):
        g.datastore = data.Store(app.config)
    return g.datastore

def wants_json():
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json" and \
            request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

def failed_auth():
    if request.accept_mimetypes.accept_html:
        return redirect(url_for('login'))
    return abort(403)

auth = Authenticator(get_datastore, failed_auth)

@oauth.clientgetter
def load_client(client_id):
    return get_datastore().fetch_client({"id": client_id})

@oauth.grantgetter
def load_grant(client_id, code):
    return get_datastore().get_grant(client_id, code)

@oauth.grantsetter
def save_grant(client_id, code, req, *args, **kwargs):
    max_grant_age = app.config.get("MAX_GRANT_AGE", 100)
    expires = datetime.utcnow() + timedelta(seconds = max_grant_age)
    redirect_uri = req.redirect_uri
    scopes = req.scopes
    code = code['code']
    with get_datastore() as store:
        client = store.fetch_client({"id": client_id})
        user = store.fetch_user(**session["user"])
        grant = store.add_grant(user, client, code, redirect_uri, scopes, expires)
    return grant

@oauth.tokengetter
def load_token(**kwargs):
    keys = ["access_token", "refresh_token"]
    with get_datastore() as store:
        return store.get_token(select_keys(kwargs, keys))

@oauth.tokensetter
def save_token(token, req, *args, **kwargs):
    with get_datastore() as store:
        client = store.fetch_client({"id": req.client.client_id})
        user = store.fetch_user({"id": req.user.id})
        return store.add_token(client, user, token)

@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    with get_datastore() as store:
        user = store.fetch_user({"name": username})
        if user and test_pw(password, user.passhash):
            return user
    return None

@app.route('/oauth2/authorize', methods = ['GET', 'POST'])
@auth.requires_roles('user')
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        with get_datastore() as store:
            client = store.fetch_client({"id": client_id})
            kwargs['client'] = client
        return render_template('oauthorize.html', **kwargs)
    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'

@app.route('/oauth2/token')
@oauth.token_handler
def access_token():
    return {'version': '0.1.0'}

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'datastore'):
        g.datastore.close()

@app.route("/")
def hello():
    return redirect(url_for('show_histories'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        store = get_datastore()
        user = store.fetch_user(name = request.form['username'])
        if user is None:
            error = 'Invalid username'
        elif not test_pw(request.form['password'], user.passhash):
            error = 'Invalid password'
        else:
            return login_user(user)
    return render_template('login.html', error=error)

def login_user(user):
    session['logged_in'] = True
    session['user'] = {"name": user.name, "id": user.id}
    return redirect(url_for('show_histories'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

def return_step(step, code = 200, headers = None):
    if wants_json():
        payload = json.jsonify(
                tool_url = step.tool,
                mimetype = step.mimetype,
                data = step.data)
    else:
        payload = render_template("show_step", step = step)

    return payload, code, headers

@app.route("/histories/<uuid>/<int:idx>")
@auth.requires_roles("user")
def show_step(uuid, idx):
    store = get_datastore()
    h = store.fetch_history(id = uuid)
    if h is None or len(h.steps) <= idx:
        return abort(404)
    step = h.steps[idx]
    return return_step(step)

@app.route('/histories/<uuid>/<int:idx>/next', methods = ['POST'])
@auth.requires_roles('user')
def add_next_step(uuid, idx):
    with get_datastore() as store:
        h      = store.fetch_history(id = uuid)
        step_data = request.json
        next_i = idx + 1

        if h is None: return abort(404)
        if step_data is None: raise InputError("Missing required data")
        args = select_keys(step_data, ['tool', 'mimetype', 'data'])

        if len(h.steps) == next_i:
            step = h.append_step(**args)
            url = url_for('show_step', uuid = h.id, idx = next_i)
        else:
            forked = store.fork_history({'id': h.id}, next_i)
            step = forked.append_step(**args)
            url = url_for('show_step', uuid = forked.id, idx = next_i)

    return return_step(step, 201, [('Location', url)])

@app.errorhandler(InputError)
def handle_input_error(err):
    return make_response(standard_response(None, 400, err.message), 400)

@app.route('/histories/<uuid>', methods = ['POST'])
@auth.requires_roles('user')
@produces('application/json', 'text/html')
def add_step(uuid):
    with get_datastore() as store:
        store     = get_datastore()
        h         = store.fetch_history(id = uuid)
        step_data = request.json

        if h is None: return abort(404)
        if step_data is None: raise InputError("Missing required data")

        step = h.append_step(step_data['tool'], step_data['mimetype'],
                step_data['data'])
        url = url_for('show_step', uuid = uuid, idx = len(h.steps) - 1)
    return return_step(step, 201, [('Location', url)])

@app.route('/histories/<uuid>', methods = ['GET'])
@auth.requires_roles('user')
@produces('application/json', 'text/html')
def show_history(uuid):
    store = get_datastore()
    h = store.fetch_history(id = uuid)
    if h is None:
        return abort(404)
    indexed_steps = zip(h.steps, range(len(h.steps)))
    steps = [ {"url": url_for("show_step", uuid = h.id, idx = i), "created_at": s.created_at} \
            for s, i in indexed_steps]
    if wants_json():
        return json.jsonify(name = h.name, created_at = h.created_at, steps = steps)
    else:
        return render_template('show_history.html', history = history, steps = indexed_steps)

@app.route('/histories', methods=['GET'])
@auth.requires_roles('user')
@produces('application/json', 'text/html')
def show_histories():
    user = get_datastore().fetch_user(**session["user"])
    hs = [ {"url": url_for('show_history', uuid = h.id), "created_at": h.created_at} \
            for h in user.histories]
    if wants_json():
        return json.jsonify(histories = hs)
    else:
        return render_template('show_histories.html', histories = user.histories)

@app.route('/histories', methods=['POST'])
@auth.requires_roles('user')
@produces('application/json', 'text/html')
def create_history():
    with get_datastore() as store:
        user = store.fetch_user(**session["user"])
        name = request.form['histname']
        history = user.new_history(name)
    url = url_for('show_history', uuid = history.id)
    if wants_json():
        return json.jsonify(history = url), 201, [('Location', url)]
    else:
        return redirect(url)

@app.route('/register', methods=['GET'])
@produces('text/html')
def register(): return render_template('register.html')

@app.route('/register', methods=["POST"])
@produces('text/html', 'application/json')
def create_user():
    data = select_keys(request.form, ["username", "password", "email"], {"username": "name"})
    if data["password"] != request.form["confirmpassword"]:
        return redirect(url_for('register', error = "Passwords do not match"))
    with get_datastore() as store:
        user = store.add_user(data)
        return login_user(user)

if __name__ == "__main__":
    init_db()
    app.run(debug = True)
