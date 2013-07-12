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
from sets import Set


"""
Re-usable structs
"""
abc_jobs = [{"job_secret": "aaa"},
            {"job_secret": "bbb"},
            {"job_secret": "ccc"}]
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

    def add_jobs(self, jobs, password, mode="append", timeout=600):
        data = {"jobs": jobs,
                "administrator_id": self.admin_id,
                "timeout": timeout,
                "mode": mode,
                "password": password}

        return self.app.post('/add', data=json.dumps(data),
            content_type='application/json', follow_redirects=True)

    def get_job(self, admin_id = None):
        aid = self.admin_id
        if admin_id is not None:
            aid = admin_id

        data = {"administrator_id": aid}

        return self.app.post('/get', content_type='application/json',
            data=json.dumps(data))

    def confirm_job(self, job_id. admin_id = None):
        aid = self.admin_id
        if admin_id is not None:
            aid = admin_id

        data = {"administrator_id": aid,
                "job_id": job_id}

        return self.app.post('/confirm', content_type='application/json',
            data=json.dumps(data))

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

        self.job_id = json.loads(rv.data)['job_id']

        if self.job_time >= 0:
            time.sleep(self.job_time)
            rv = self.app.confirm_job(self.job_id)
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
        administrator.app.config['ENFORCE_JOB_TYPES'] = True
        administrator.app.config['PASSWORD_HASH'] = administrator.hash_password('real_password')
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
        self.assertEqual(403, rv.status_code)
        self.assertIn("Password invalid", rv.data)

        rv = self.app.add_jobs(abc_jobs, "real_password")
        self.assertEqual(200, rv.status_code)
        self.assertIn("Jobs appended", rv.data)

    def test_add_jobs_populate(self):
        rv = self.app.add_jobs(abc_jobs, "real_password", "populate")
        self.assertIn("Jobs appended", rv.data)

        rv = self.app.add_jobs(abc_jobs, "real_password", "populate")
        self.assertIn("Not repopulating jobs", rv.data)

    def test_add_jobs_replace(self):
        rv = self.app.add_jobs(abc_jobs, "real_password", "append")
        self.assertIn("Jobs appended", rv.data)

        rv = self.app.add_jobs(abc_jobs, "real_password", "replace")
        self.assertIn("Jobs replaced", rv.data)

    def test_get_job_empty(self):
        rv = self.app.get_job()
        self.assertEqual(503, rv.status_code)
        self.assertIn("No jobs available", rv.data)

    def test_get_job(self):
        log = logging.getLogger( "AdministratorTests.test_get_job")
        
        rv = self.app.add_jobs(abc_jobs, "real_password")

        log.debug("abc_aid = %s", abc_aid)
        rv = self.app.get_job()
        log.debug("get_job response mimetype is '%s'", rv.mimetype)
        log.debug("get_job response payload is '%s'", rv.data)
        self.assertEqual(200, rv.status_code)
        self.assertEqual(rv.mimetype, 'application/json')

        payload = json.loads(rv.data)["payload"]
        self.assertIn(payload["job_secret"], "aaabbbccc")

    def test_get_job_twice(self):
        rv = self.app.add_jobs(abc_jobs, "real_password")
        rv = self.app.get_job()

        job_id = json.loads(rv.data)['job_id']
        rv = self.app.get_job()

        self.assertEqual(json.loads(rv.data)['job_id'], job_id)

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

    def test_exhaust_jobs(self):
        self.app.add_jobs(abc_jobs, "real_password")

        app2 = HelperApp(abc_aid)
        app3 = HelperApp(abc_aid)
        app4 = HelperApp(abc_aid)
        
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id1 = json.loads(rv.data)['job_id']
        rv = app2.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id2 = json.loads(rv.data)['job_id']
        rv = app3.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id3 = json.loads(rv.data)['job_id']

        self.app.confirm_job(job_id1)
        app2.confirm_job(job_id2)
        app3.confirm_job(job_id3)

        rv = app4.get_job()
        self.assertIn("No jobs available", rv.data)

    def test_hand_out_pending(self):
        self.app.add_jobs(abc_jobs, "real_password")

        app2 = HelperApp(abc_aid)
        app3 = HelperApp(abc_aid)
        app4 = HelperApp(abc_aid)
        
        rv = self.app.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id1 = json.loads(rv.data)['job_id']
        rv = app2.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id2 = json.loads(rv.data)['job_id']
        rv = app3.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id3 = json.loads(rv.data)['job_id']

        rv = app4.get_job()
        self.assertNotIn("No jobs available", rv.data)
        job_id4 = json.loads(rv.data)['job_id']

        self.assertIn(job_id4, [job_id1, job_id2, job_id3])

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

    def test_all_jobs_unique(self):
        many = 25
        self.app.add_jobs(gen_n_jobs(many), "real_password")
        workers = [Worker(abc_aid, 1) for i in range(many)]
        for w in workers:
            w.start()

        [w.join() for w in workers]

        ids = Set()
        for w in workers:
            ids.add(w.job_id)

        self.assertEqual(len(ids), many)

    def test_many_workers(self):
        many = 25
        self.app.add_jobs(gen_n_jobs(many), "real_password")
        workers = [Worker(abc_aid, 1) for i in range(many)]
        for w in workers:
            w.start()

        [w.join() for w in workers]

        self.assertListEqual([w.success for w in workers],
                             [True for w in workers])

    def test_no_same_job_type_twice(self):
        """
        Test that we can't get a job of the same type, even on
        a different administrator id
        """

        second_aid = "abc2"

        app2 = HelperApp(second_aid)

        self.app.add_jobs(abc_jobs, "real_password")
        app2.add_jobs(abc_jobs, "real_password")

        rv = self.app.get_job()
        payload = json.loads(rv.data)["payload"]

        self.assertIn(payload["job_secret"], "aaabbbccc")
        
        job_id = json.loads(rv.data)['job_id']
        self.app.confirm_job(job_id)

        # Get the two jobs that are different from first
        for i in range(2):
            rv = self.app.get_job(second_aid)
            pl = json.loads(rv.data)["payload"]
            self.assertIn(pl["job_secret"], "aaabbbccc")
            self.assertNotEqual(payload, pl)

            print pl

            job_id = json.loads(rv.data)['job_id']
            self.app.confirm_job(job_id, second_aid)

        # Try and get a third job and fail
        rv = self.app.get_job(second_aid)
        self.assertIn("No jobs available", rv.data)

    def test_random_no_exceptions(self):
        many = 100
        workers = [Worker(abc_aid, randint(0, many), randint(0, many)) for i in range(many)]

        for w in workers:
            w.start()

        for w in workers:
            w.join()


if __name__ == '__main__':
    unittest.main()