CREATE TABLE IF NOT EXISTS administrators (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	administrator_id TEXT,
	json TEXT,
    timeout INTEGER,
    status TEXT,
    claimant_uuid TEXT,
    expire_time TIMESTAMP,
	FOREIGN KEY(administrator_id) REFERENCES administrators(id)
);