from flask import Flask, g, flash, request, session, redirect, url_for, abort, \
     render_template, flash, json

import os.path as path

import snakepit
from snakepit.security import test_pw, Authenticator

templates = path.realpath(path.join(path.dirname(__file__), "..", "templates"))

app = Flask(__name__, template_folder = templates)
app.config.update(snakepit.config.Config())

def init_db():
    """Creates the database tables."""
    with app.app_context():
        get_datastore().create_db()

def get_datastore():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'datastore'):
        g.datastore = snakepit.data.Store(app.config)
    return g.datastore

auth = Authenticator(get_datastore)

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'datastore'):
        g.datastore.close()

@app.route("/")
def hello():
    return "Hello World!"

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
            session['logged_in'] = True
            session['user'] = {"name": user.name, "id": user.id}
            return redirect(url_for('show_histories'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

@app.route("/histories/<uuid>/<int:idx>")
@auth.requires_roles("user")
def show_step(uuid, idx):
    store = get_datastore()
    h = store.fetch_history(id = uuid)
    if h is None or len(h.steps) <= idx:
        return abort(404)
    step = h.steps[idx]
    return json.jsonify(mimetype = step.mimetype, data = step.data)

@app.route('/histories/<uuid>')
@auth.requires_roles('user')
def show_history(uuid):
    store = get_datastore()
    h = store.fetch_history(id = uuid)
    if h is None:
        return abort(404)
    steps = [ {"url": url_for("show_step", uuid = s.id), "created_at": s.created_at} \
            for s in h.steps ]
    return json.jsonify(name = h.name, created_at = h.created_at, steps = steps)

@app.route('/histories')
@auth.requires_roles('user')
def show_histories():
    user = get_datastore().fetch_user(**session["user"])
    hs = [ {"url": url_for('show_history', uuid = h.id), "created_at": h.created_at} \
            for h in user.histories]
    return json.jsonify(histories = hs)

if __name__ == "__main__":
    init_db()
    app.run()
