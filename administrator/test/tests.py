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
        return self.app.post('/add', data=dict(
          jobs=json.dumps(jobs),
          password=password), follow_redirects=True)

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
        # logging.getLogger("AdministratorTests.test_db_has_administrator_table").setLevel(logging.DEBUG)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(administrator.app.config['DATABASE'])

    def test_add_jobs_password(self):
        log = logging.getLogger( "AdministratorTests.test_db_has_administrator_table")
        rv = self.add_jobs([{"job_secret": "a"},
            {"job_secret": "b"},
            {"job_secret": "c"}], "fake_password")
        self.assertIn("Password invalid", rv.data)

        rv = self.add_jobs([{"job_secret": "a"},
            {"job_secret": "b"},
            {"job_secret": "c"}], "real_password")
        self.assertIn("Jobs added", rv.data)



if __name__ == '__main__':
    unittest.main()