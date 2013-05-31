from flask import Flask
import sqlite3 as sql
app = Flask(__name__)

DATABASE = '~/administrator.db'


"""
Initialize, connect to the db
Note that SQLite3 commands automatically create
transactions if one does not already exist
"""

def connect_db():
	return sql.connect(DATABASE)

@app.before_request
def before_request():
    g.db = connect_db()
app
@.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

"""
Add jobs to the db
"""

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host='0.0.0.0')