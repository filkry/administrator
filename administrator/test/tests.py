import unittest
import tempfile
import os
import logging
import administrator
import sys
import json

class AdministratorTests(unittest.TestCase):


    """
    Request convenience methods
    """

    def add_jobs(self, jobs, password):
        return self.app.get('/add')
        # return self.app.post('/add', data=dict(
        #   jobs=json.dumps(jobs),
        #   password=password), follow_redirects=True))

    """
    Test setUp
    """

    def setUp(self):
        self.db_fd, administrator.app.config['DATABASE'] = tempfile.mkstemp()
        administrator.app.config['TESTING'] = True
        self.app = administrator.app.test_client()
        administrator.init_db()

        # Set up logging if you want
        logging.basicConfig( stream=sys.stderr )
        logging.getLogger("AdministratorTests.test_db_has_administrator_table").setLevel(logging.DEBUG)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(administrator.app.config['DATABASE'])

    def test_db_not_empty(self):
        """
        Ensure there's *something* in the DATABASE
        """
        with administrator.connect_db() as db:
          log = logging.getLogger( "AdministratorTests.test_db_not_empty")
          c = db.cursor()
          c.execute("SELECT COUNT(*) FROM sqlite_master;")

          row = c.fetchone()
          log.debug(row)

          self.assertGreater(row[0], 0)

    def test_db_has_administrator_table(self):
        """
        Ensure administrator table in the DATABASE
        """
        with administrator.connect_db() as db:
          c = db.cursor()
          c.execute("""SELECT COUNT(name) FROM sqlite_master 
            WHERE type='table' AND name='administrators';""")

          row = c.fetchone()
          self.assertEqual(row[0], 1)

    def test_db_has_administrator_table(self):
        """
        Ensure jobs table in the DATABASE
        """
        with administrator.connect_db() as db:
          c = db.cursor()
          c.execute("""SELECT COUNT(name) FROM sqlite_master 
            WHERE type='table' AND name='jobs';""")

          row = c.fetchone()
          self.assertEqual(row[0], 1)

    def test_add_jobs(self):
        log = logging.getLogger( "AdministratorTests.test_db_has_administrator_table")
        rv = self.add_jobs([{"job_secret": "a"},
            {"job_secret": "b"},
            {"job_secret": "c"}], "fake_password")
        log.debug(rv)

        if __name__ == '__main__':
          unittest.main()