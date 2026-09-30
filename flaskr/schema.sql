-- Drop existing tables
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS craigslist_postings;
DROP TABLE IF EXISTS craigslist_jobs;
DROP TABLE IF EXISTS chart;
DROP TABLE IF EXISTS gallery;
DROP TABLE IF EXISTS network_logs;
DROP TABLE IF EXISTS astronomy;
DROP TABLE IF EXISTS search_query;
DROP TABLE IF EXISTS system_logs;

-- Users table
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

-- Posts table
CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body BLOB NOT NULL,
  image TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  FOREIGN KEY (author_id) REFERENCES user (id) ON DELETE CASCADE
);

CREATE INDEX idx_post_author_id ON post(author_id);

-- Craigslist postings table
CREATE TABLE craigslist_postings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  craigslist_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  price_text TEXT,
  price_amount REAL,
  location TEXT,
  latitude REAL,
  longitude REAL,
  listing_url TEXT NOT NULL,
  category TEXT,
  search_query TEXT,
  posted_at TEXT,
  scraped_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  image_url TEXT,
  description TEXT,
  blog_post_id INTEGER,
  FOREIGN KEY (blog_post_id) REFERENCES post(id) ON DELETE SET NULL
);

CREATE INDEX idx_craigslist_postings_posted_at
  ON craigslist_postings(posted_at DESC);

-- Craigslist jobs configuration table
CREATE TABLE craigslist_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  term TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('pet', 'sss', 'zip')),
  radius INTEGER NOT NULL DEFAULT 100,
  run_times TEXT NOT NULL DEFAULT '06:00',
  location_name TEXT NOT NULL DEFAULT 'East Texas',
  location_url TEXT NOT NULL DEFAULT 'https://www.craigslist.org/search/area/easttexas',
  is_default_location INTEGER NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1,
  last_run_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_craigslist_jobs_enabled
  ON craigslist_jobs(enabled);

CREATE UNIQUE INDEX idx_craigslist_jobs_default_location
  ON craigslist_jobs(is_default_location) WHERE is_default_location = 1;

-- Weather / chart table
CREATE TABLE chart (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at DATETIME DEFAULT (datetime('now', 'localtime')),
  location TEXT NOT NULL,
  geolocation TEXT,
  description TEXT,
  temperature REAL,
  pressure INTEGER,
  feelslike REAL,
  humidity INTEGER,
  visibility INTEGER,
  windspeed REAL,
  winddirection INTEGER,
  clouds INTEGER,
  sunrise DATETIME,
  sunset DATETIME,
  dew_point REAL GENERATED ALWAYS AS (
    CAST(ROUND(
        (237.3 * (ln(humidity / 100.0) + ((17.27 * temperature) / (temperature + 237.3)))) / 
        (17.27 - (ln(humidity / 100.0) + ((17.27 * temperature) / (temperature + 237.3))))
    ) AS INTEGER)        
  ) STORED
);

-- Gallery table
CREATE TABLE gallery (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  image_data BLOB NOT NULL
);

-- Network logs table
CREATE TABLE network_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL DEFAULT (DATETIME('now')),
  source_ip TEXT NOT NULL,
  source_port INTEGER,
  dest_ip TEXT NOT NULL,
  dest_port INTEGER,
  protocol TEXT NOT NULL,
  bytes_sent INTEGER DEFAULT 0,
  bytes_received INTEGER DEFAULT 0,
  status TEXT,
  message TEXT
);

CREATE INDEX idx_network_logs_timestamp ON network_logs(timestamp);
CREATE INDEX idx_network_logs_source_ip ON network_logs(source_ip);

-- Astronomy table
CREATE TABLE astronomy (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL DEFAULT (DATETIME('now')),
  location TEXT,
  country_name TEXT,
  state_prov TEXT,
  city TEXT,
  locality TEXT,
  latitude REAL,
  longitude REAL,
  elevation REAL,
  mid_night TEXT,
  night_end TEXT,
  morn_astronomical_twilight_begin TEXT,
  morn_astronomical_twilight_end TEXT,
  morn_nautical_twilight_begin TEXT,
  morn_nautical_twilight_end TEXT,
  morn_civil_twilight_begin TEXT,
  morn_civil_twilight_end TEXT,
  morn_blue_hour_begin TEXT,
  morn_blue_hour_end TEXT,
  morn_golden_hour_begin TEXT,
  morn_golden_hour_end TEXT, 
  sunrise TEXT,
  sunset TEXT,
  eve_golden_hour_begin TEXT,
  eve_golden_hour_end TEXT,
  eve_blue_hour_begin TEXT,
  eve_blue_hour_end TEXT,
  eve_civil_twilight_begin TEXT,
  eve_civil_twilight_end TEXT,
  eve_nautical_twilight_begin TEXT,
  eve_nautical_twilight_end TEXT,
  eve_astronomical_twilight_begin TEXT,
  eve_astronomical_twilight_end TEXT,
  night_begin TEXT,
  sun_status TEXT,
  solar_noon TEXT,
  day_length TEXT,
  sun_altitude REAL,
  sun_distance REAL,
  sun_azimuth REAL,
  moon_phase TEXT,
  moonrise TEXT,
  moonset TEXT,
  moon_status TEXT,
  moon_altitude REAL,
  moon_distance REAL,
  moon_azimuth REAL,
  moon_parallactic_angle REAL,
  moon_illumination_percentage REAL,
  moon_angle REAL
);

-- Search queries tracking
CREATE TABLE search_query (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  term TEXT NOT NULL,
  radius INTEGER NOT NULL,
  status TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- System logs table
CREATE TABLE system_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  level TEXT NOT NULL,
  logger TEXT NOT NULL,
  message TEXT NOT NULL,
  pathname TEXT,
  line_number INTEGER,
  exception TEXT
);

CREATE INDEX idx_system_logs_created_at
  ON system_logs(created_at DESC);