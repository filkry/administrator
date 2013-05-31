import unittest
import tempfile
import os
import administrator

class AdministratorTests(unittest.TestCase):

  def setUp(self):
    self.db_fd, administrator.app.config['DATABASE'] = tempfile.mkstemp()
    administrator.app.config['TESTING'] = True
    self.app = administrator.app.test_client()
    administrator.init_db()

  def tearDown(self):
    os.close(self.db_fd)
    os.unlink(administrator.app.config['DATABASE'])

  def test_db_has_administrator_table(self):
    """
    Ensure there's an administrator table in the DATABASE
    """
    with administrator.connect_db() as db:
      c = db.cursor()
      c.execute("SELECT * FROM sqlite_master;")
      rows = ','.join(c.fetchall())
      self.assertRegexpMatches(rows, ".*table|administrators|.*")