CREATE TABLE IF NOT EXISTS jobs (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	administrator_id TEXT,
	job_type TEXT,
	json TEXT,
    timeout INTEGER,
    status TEXT,
    claimant_uuid TEXT,
    expire_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_job_types (
	uuid TEXT,
	job_type TEXT
);