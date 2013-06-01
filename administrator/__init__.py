from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
from contextlib import closing
import sqlite3
import md5
app = Flask(__name__)

"""
Embedded config
"""

DATABASE = '~/administrator.db'
PASSWORD_HASH = md5.new('real_password').digest()

"""
Set up as app
"""
app = Flask(__name__)
app.config.from_object(__name__)


"""
Helper methods
"""

def hash_password(pw):
    """
    This uses unsalted md5 for now, as my use case does not
    require a lot of security to merit additional effort.
    """
    return md5.new(pw).digest()

"""
Initialize, connect to the db
Note that SQLite3 commands automatically create
transactions if one does not already exist
"""

def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema/administrator.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'])
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db

    return top.sqlite_db

@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

"""
Add jobs to the db
"""

@app.route("/add", methods=['POST'])
def add():
    if hash_password(request.form['password']) == app.config['PASSWORD_HASH']:
        return "Jobs added"
    else:
        return "Password invalid"
