CREATE TABLE IF NOT EXISTS administrators (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT)

/*CREATE TABLE IF NOT EXISTS jobs (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	administrator_id INTEGER,
	job_json TEXT,
	FOREIGN_KEY(administrator_id) REFERENCES administrators(id)
);*/