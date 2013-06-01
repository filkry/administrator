from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, jsonify
from contextlib import closing
import sqlite3
import md5
import json
app = Flask(__name__)

"""
Embedded config
"""

DATABASE = '~/administrator.db'
PASSWORD_HASH = md5.new('fancy').digest()

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
        sqlite_db = sqlite3.connect(app.config['DATABASE'],
                                    isolation_level=None)
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
        jobs = json.loads(request.form['jobs'])
        insert_tuples = [(request.form['administrator_id'],
                          json.dumps(j)) for j in jobs]
        db = get_db()
        c = db.cursor()
        c.executemany("INSERT INTO jobs (administrator_id, json, status) \
            VALUES (?, ?, 'ready')", insert_tuples)
        db.commit()
        return "Jobs added"
    else:
        return "Password invalid"

@app.route("/get", methods=['Post'])
def get():
    db = get_db()
    c = db.cursor()
    aid = request.form['administrator_id']
    c.execute("BEGIN")
    c.execute("SELECT id, json FROM jobs \
        WHERE administrator_id=? and status='ready' \
        ORDER BY RANDOM() LIMIT 1;", (aid, ))

    c_res = c.fetchone()

    if c_res is None:
        c.execute("COMMIT")
        return "No jobs available"

    job_id, payload = c_res[0], c_res[1]
    c.execute("UPDATE jobs SET status='pending' \
        WHERE id=?;", (job_id, ))
    c.execute("COMMIT")
    db.commit()

    payload = json.loads(payload)
    resp = {'job_id': job_id,
            'payload': payload}

    return jsonify(resp)

@app.route("/confirm", methods=['Post'])
def confirm():
    db = get_db()
    c = db.cursor()

    aid = request.form['administrator_id']
    job_id = request.form['job_id']

    c.execute("BEGIN")
    c.execute("SELECT COUNT(*) FROM jobs \
        WHERE administrator_id=? and \
        id=? and status='pending'", (aid, job_id))

    if c.fetchone()[0] != 1:
        return "Job not confirmed; does not exist, not taken, or already complete"

    c.execute("UPDATE jobs SET status='complete' \
        WHERE administrator_id=? and \
        id=? and status='pending'", (aid, job_id))

    c.execute("COMMIT")
    db.commit()

    return "Job confirmed complete"

