CREATE TABLE IF NOT EXISTS chart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
    location TEXT,
    geolocation TEXT,
    description TEXT,
    tempurature TEXT,
    pressure TEXT,
    feelslike TEXT,
    humidity TEXT,
    visibility TEXT,
    windspeed TEXT,
    winddirection TEXT,
    clouds TEXT,
    sunrise TEXT,
    sunset TEXT
);


