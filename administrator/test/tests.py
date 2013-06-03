import unittest
import tempfile
import os
import logging
import administrator
import sys
import json
import md5
import time
import threading
from random import randint


"""
Re-usable structs
"""
abc_jobs = [{"job_secret": "a"},
            {"job_secret": "b"},
            {"job_secret": "c"}]
abc_aid = "abc"

def gen_n_jobs(n):
    return [{"job_secret": x} for x in range(n)]

"""
Helper classes
"""

class HelperApp():
    def __init__(self, admin_id):
        self.app = administrator.app.test_client()
        self.admin_id = admin_id

    def add_jobs(self, jobs, password, timeout=600):
        return self.app.post('/add', data=dict(
          jobs=json.dumps(jobs),
          administrator_id=self.admin_id,
          timeout=timeout,
          password=password), follow_redirects=True)

    def get_job(self):
        return self.app.post('/get', data=dict(
            administrator_id=self.admin_id))

    def confirm_job(self, job_id):
        return self.app.post('/confirm', data=dict(
            administrator_id=self.admin_id,
            job_id = job_id))

class Worker(threading.Thread):
    def __init__(self, admin_id, job_time, start_time = 0):
        super(Worker, self).__init__()
        self.app = HelperApp(admin_id)
        self.job_time = job_time
        self.start_time = start_time
        self.success = False
        self.reason = None

    def run(self):
        time.sleep(self.start_time)

        rv = self.app.get_job()
        if not rv.mimetype == 'application/json':
            self.reason = rv.data
            return

        job_id = json.loads(rv.data)['job_id']

        if self.job_time >= 0:
            time.sleep(self.job_time)
            rv = self.app.confirm_job(job_id)
            self.success = "Job confirmed complete" in rv.data
            if not self.success:
                self.reason = rv.data

class AdministratorTests(unittest.TestCase):

    """
    Assumptions we make in these tests due to the limited
    scope of the project:
        * we always receive well-formed input
        * users may accidentely quit a session, but will not switch computers
    """
    
    """
    Test setUp
    """

    def setUp(self):
        self.db_fd, administrator.app.config['DATABASE'] = tempfile.mkstemp()
        administrator.app.config['TESTING'] = True
        administrator.app.config['PASSWORD_HASH'] = md5.new('real_password').digest()
        administrator.app.config['SECRET_KEY'] = md5.new('real_key').digest()
        self.app = HelperApp(abc_aid)
        administrator.init_db()

        # Set up logging if you want
        logging.basicConfig( stream=sys.stderr )
        # logging.getLogger("AdministratorTests.test_get_job").setLevel(logging.DEBUG)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(administrator.app.config['DATABASE'])

    def test_add_jobs_password(self):
        log = logging.getLogger( "AdministratorTests.test_db_has_administrator_table")
        rv = self.app.add_jobs(abc_jobs, "fake_password")
        self.assertIn("Password invalid", rv.data)

        rv = self.app.add_jobs(abc_jobs, "real_password")
        self.assertIn("Jobs added", rv.data)

    def test_get_job_empty(self):
        rv = self.app.get_job()
        self.assertIn("No jobs available", rv.data)

    def test_get_job(self):
        log = logging.getLogger( "AdministratorTests.test_get_job")
        
        rv = self.app.add_jobs(abc_jobs, "real_password")

        log.debug("abc_aid = %s", abc_aid)
        rv = self.app.get_job()
        log.debug("get_job response mimetype is '%s'", rv.mimetype)
        log.debug("get_job response payload is '%s'", rv.data)
        self.assertEqual(rv.mimetype, 'application/json')

        payload = json.loads(rv.data)["payload"]
        self.assertIn(payload["job_secret"], "abc")

    def test_exhaust_jobs(self):
        self.app.add_jobs(abc_jobs, "real_password")
        
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)

        rv = self.app.get_job()
        self.assertIn("No jobs available", rv.data)

    def test_confirm_job(self):
        self.app.add_jobs(abc_jobs, "real_password")
        
        rv = self.app.get_job()
        job_id = json.loads(rv.data)['job_id']

        # Can confirm a job you own
        rv = self.app.confirm_job(job_id)
        self.assertIn("Job confirmed complete", rv.data)

        # Cannot confirm same job twice
        rv = self.app.confirm_job(job_id)
        self.assertIn("Job confirm failed", rv.data)

        # Cannot confirm a job that doesn't exist
        rv = self.app.confirm_job('12345')
        self.assertIn("Job confirm failed", rv.data)

    def test_confirm_unowned_job(self):
        app2 = HelperApp(abc_aid)

        self.app.add_jobs(abc_jobs, "real_password")

        rv = app2.get_job()
        job_id = json.loads(rv.data)['job_id']

        # Can't confirm job when we don't have any
        rv = self.app.confirm_job(job_id)
        self.assertNotIn("Job confirmed complete", rv.data)
        self.assertIn("Job confirm failed", rv.data)

        # Can't confirm someone else's job
        self.app.get_job()
        rv = self.app.confirm_job(job_id)
        self.assertNotIn("Job confirmed complete", rv.data)
        self.assertIn("Job confirm failed", rv.data)

    def test_timout_success(self):
        """
        Test that we can get a job after timeout
        """

        self.app.add_jobs(abc_jobs,
            "real_password", timeout=5)
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)

        time.sleep(10)
        rv = self.app.get_job()
        self.assertNotIn("Job confirm failed", rv.data)

    def test_many_workers(self):
        many = 25
        self.app.add_jobs(gen_n_jobs(many), "real_password")
        workers = [Worker(abc_aid, 1) for i in range(many)]
        for w in workers:
            w.start()

        [w.join() for w in workers]

        self.assertListEqual([w.success for w in workers],
                             [True for w in workers])

    def test_many_workers_fail_replace(self):
        many = 24 # must be even
        self.app.add_jobs(gen_n_jobs(many), "real_password", timeout=10)

        # workers should finish quickly and on time
        fast_workers = [Worker(abc_aid, 1) for i in range(many/2)]

        # workers that will leave and never finish
        slow_workers = [Worker(abc_aid, -1) for i in range(many/2)]

        for w in fast_workers + slow_workers:
            w.start()
        [w.join() for w in fast_workers + slow_workers]

        # workers should be rejected with no jobs available
        rejected_workers = [Worker(abc_aid, 1) for i in range(many/2)]

        for w in rejected_workers:
            w.start()
        [w.join() for w in rejected_workers]

        self.assertListEqual([w.success for w in fast_workers],
                             [True for w in fast_workers])
        self.assertListEqual([w.success for w in rejected_workers],
                             [False for w in rejected_workers])

        # wait for jobs to expire
        time.sleep(10)

        # workers should get jobs now that slow_workers have expired
        replacement_workers = [Worker(abc_aid, 1) for i in range(many/2)]
        for w in replacement_workers:
            w.start()

        [w.join() for w in replacement_workers]

        self.assertListEqual([w.success for w in replacement_workers],
                             [True for w in replacement_workers])

    def test_random_no_exceptions(self):
        many = 100
        workers = [Worker(abc_aid, randint(0, many), randint(0, many)) for i in range(many)]

        for w in workers:
            w.start()

        for w in workers:
            w.join()


if __name__ == '__main__':
    unittest.main()