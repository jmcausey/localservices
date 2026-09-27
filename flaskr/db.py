import sqlite3
from datetime import datetime

import click
from flask import current_app, g


CREATE_CRAIGSLIST_POSTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS craigslist_postings (
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
)
"""

CREATE_CRAIGSLIST_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS craigslist_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    term TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('pet', 'sss', 'zip')),
    radius INTEGER NOT NULL DEFAULT 100,
    run_times TEXT NOT NULL DEFAULT '06:00',
    enabled INTEGER NOT NULL DEFAULT 1,
    last_run_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

def ensure_craigslist_postings_table(database_path):
    with sqlite3.connect(database_path) as connection:
        connection.execute(CREATE_CRAIGSLIST_POSTINGS_TABLE)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_craigslist_postings_posted_at "
            "ON craigslist_postings(posted_at DESC)"
        )


def ensure_craigslist_jobs_table(database_path):
    default_jobs = (
        ("pets", "East Texas Pets", "pets", "pet", 100, "06:00"),
        ("surfboards", "Surfboards", "surfboard", "sss", 100, "08:00,20:00"),
        ("free-stuff", "Free Stuff", "free stuff", "zip", 100, "08:00,20:00"),
    )
    with sqlite3.connect(database_path) as connection:
        connection.execute(CREATE_CRAIGSLIST_JOBS_TABLE)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_craigslist_jobs_enabled "
            "ON craigslist_jobs(enabled)"
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO craigslist_jobs
                (job_key, name, term, category, radius, run_times)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            default_jobs,
        )


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    ensure_craigslist_postings_table(app.config['DATABASE'])
    ensure_craigslist_jobs_table(app.config['DATABASE'])

