from flask import Flask
import sqlite3
app = Flask(__name__)

"""
Embedded config
"""

DATABASE = '~/administrator.db'

"""
Set up as app
"""
app = Flask(__name__)
app.config.from_object(__name__)

"""
Initialize, connect to the db
Note that SQLite3 commands automatically create
transactions if one does not already exist
"""

def init_db():
  with connect_db() as db:
    with app.open_resource('schema/administrator.sql') as f:
      db.cursor().executescript(f.read())
    db.commit()

def connect_db():
  return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
  g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
  if hasattr(g, 'db'):
    g.db.close()

"""
Add jobs to the db
"""

@app.route("/")
def hello():
  return "Hello World!"