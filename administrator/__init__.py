from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, jsonify
from contextlib import closing # TODO: remove this?
from datetime import datetime, timedelta
import sqlite3
import md5
import json
import uuid
import threading
app = Flask(__name__)

"""
Embedded config
"""

DATABASE = '~/administrator.db'
PASSWORD_HASH = md5.new('fancy').digest()
SECRET_KEY = md5.new('fancy').digest()

"""
Set up as app
"""
app = Flask(__name__)
app.config.from_object(__name__)


"""
Locks

Wanted to avoid this but was spending too much time on
debugging atomicity in sqlite3
"""

get_lock = threading.Lock()

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

@app.route("/")
def hello_world():
    return "Hello world"

@app.route("/add", methods=['POST'])
def add():
    if hash_password(request.form['password']) == app.config['PASSWORD_HASH']:
        jobs = json.loads(request.form['jobs'])
        timeout = request.form['timeout']
        insert_tuples = [(request.form['administrator_id'],
                          json.dumps(j),
                          timeout) for j in jobs]
        db = get_db()

        with closing(db.cursor()) as c:
            try:
                c.executemany("INSERT INTO jobs (administrator_id, json, timeout, status) \
                    VALUES (?, ?, ?, 'ready')", insert_tuples)
            except:
                print "Unexpected error add"
        
        return "Jobs added"
    else:
        return "Password invalid"


def expire_jobs(db):
    timestamp = datetime.utcnow()
    
    with closing(db.cursor()) as c:
        try:
            c.execute("UPDATE jobs SET status='ready'  \
                WHERE status='pending' and expire_time < ?",
                (timestamp,))
        except Exception,e:
            print str(e)


@app.route("/get", methods=['Post'])
def get():
    if not 'user_id' in session:
        session['user_id'] = uuid.uuid4().hex

    aid = request.form['administrator_id']

    db = get_db()
    expire_jobs(db)

    with get_lock:
        with closing(db.cursor()) as c:
            try:
                c.execute("SELECT id, json, timeout FROM jobs WHERE administrator_id=? \
                    and status='ready' ORDER BY RANDOM() LIMIT 1", (aid,))

                c_res = c.fetchone()
                if c_res is None:
                    return "No jobs available"

                job_id, payload, timeout = c_res
                expire_time = datetime.utcnow() + timedelta(seconds=timeout)
                
                c.execute("UPDATE jobs SET status='pending', claimant_uuid=?, \
                            expire_time=? WHERE id = ?",
                            (session['user_id'], expire_time, job_id))
            except Exception,e:
                print str(e)

    payload = json.loads(payload)
    resp = {'job_id': job_id,
            'payload': payload}

    return jsonify(resp)

@app.route("/confirm", methods=['Post'])
def confirm():
    if not 'user_id' in session:
        session['user_id'] = uuid.uuid4().hex

    aid = request.form['administrator_id']
    job_id = request.form['job_id']

    db = get_db()
    try:
        with closing(db.cursor()) as c:
            c.execute("UPDATE jobs SET status='complete' \
                WHERE administrator_id=? and \
                id=? and status='pending' and \
                claimant_uuid=?", (aid, job_id, session['user_id']))

            if c.rowcount != 1:
                return "Job confirm failed. Job does not exist, was not begun, \
                    already complete, timed out, or belongs to another user"
    except:
        print "Unexpected error confirm"

    return "Job confirmed complete"

if __name__ == "__main__":
    app.run()
    app.init_db()