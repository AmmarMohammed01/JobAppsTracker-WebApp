-- SQLite schema for `jobapps` (converted from MySQL dump)
-- Foreign keys are off by default in SQLite; enable per connection:
PRAGMA foreign_keys = ON;

-- jobapps user, attached to job listing
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE category (
  category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  category_name TEXT UNIQUE COLLATE NOCASE
);

CREATE TABLE company (
  company_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE platform (
  platform_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  platform_name TEXT UNIQUE COLLATE NOCASE
);

CREATE TABLE resume (
  resume_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  resume_name TEXT COLLATE NOCASE,
  user_id     INTEGER REFERENCES user (id) ON DELETE CASCADE,
  UNIQUE (user_id, resume_name)
);
CREATE INDEX idx_resume_user ON resume (user_id);

CREATE TABLE job (
  job_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER REFERENCES user (id) ON DELETE CASCADE,
  company_id  INTEGER REFERENCES company (company_id)  ON DELETE SET NULL,
  platform_id INTEGER REFERENCES platform (platform_id) ON DELETE SET NULL,
  job_title   TEXT NOT NULL,
  resume_id   INTEGER REFERENCES resume (resume_id)    ON DELETE SET NULL
);
CREATE INDEX idx_job_company  ON job (company_id);
CREATE INDEX idx_job_platform ON job (platform_id);
CREATE INDEX idx_job_resume   ON job (resume_id);
CREATE INDEX idx_job_user     ON job (user_id);

CREATE TABLE category_to_job (
  category_id INTEGER NOT NULL REFERENCES category (category_id),
  job_id      INTEGER NOT NULL REFERENCES job (job_id),
  PRIMARY KEY (category_id, job_id)
);
CREATE INDEX idx_category_to_job_job ON category_to_job (job_id);

-- website login
CREATE TABLE login (
  login_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER REFERENCES company (company_id) ON DELETE CASCADE,
  username   TEXT NOT NULL,
  password   TEXT
);
CREATE INDEX idx_login_company ON login (company_id);

CREATE TABLE status (
  status_id          INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id             INTEGER REFERENCES job (job_id) ON DELETE CASCADE,
  status_datetime    TEXT NOT NULL,  -- store as 'YYYY-MM-DD HH:MM:SS'
  status_description TEXT NOT NULL
);
CREATE INDEX idx_status_job ON status (job_id);

CREATE TABLE url (
  link_id      INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id       INTEGER REFERENCES job (job_id) ON DELETE CASCADE,
  website_link TEXT
);
CREATE INDEX idx_url_job ON url (job_id);
