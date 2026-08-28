DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body BLOB NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE IF NOT EXISTS chart (
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

CREATE TABLE IF NOT EXISTS gallery (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  image_data BLOB NOT NULL
  );

CREATE TABLE IF NOT EXISTS network_logs (
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

CREATE INDEX IF NOT EXISTS idx_network_logs_timestamp ON network_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_network_logs_source_ip ON network_logs(source_ip);


CREATE TABLE IF NOT EXISTS astronomy (
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
q    moon_azimuth REAL,
    moon_parallactic_angle REAL,
    moon_illumination_percentage REAL,
    moon_angle REAL
);
