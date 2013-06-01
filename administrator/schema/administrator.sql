CREATE TABLE IF NOT EXISTS administrators (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	administrator_id TEXT,
	json TEXT,
    status TEXT,
    claimant_uuid TEXT,
	FOREIGN KEY(administrator_id) REFERENCES administrators(id)
);