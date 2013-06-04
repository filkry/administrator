from flask.ext.script import Manager

from administrator import app

manager = Manager(app)

@manager.command
def init_db():
    print "hello"

if __name__ == "__main__":
    manager.run()