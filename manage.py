from flask.ext.script import Manager

import administrator

manager = Manager(administrator.app)

@manager.command
def init_db():
    administrator.init_db()

if __name__ == "__main__":
    manager.run()