from datetime import datetime
import sqlite3

import pytest

from flaskr import create_app
from flaskr import craigslist_jobs
from flaskr.craigslist_jobs import run_due_craigslist_jobs
from flaskr.db import ensure_craigslist_jobs_table, get_db


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "control.sqlite"),
        }
    )
    with app.app_context():
        db = get_db()
        db.executescript(
            """
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
                image TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                FOREIGN KEY (author_id) REFERENCES user (id)
            );
            CREATE TABLE search_query (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                radius INTEGER NOT NULL,
                status TEXT NOT NULL,
                created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO user (username, password) VALUES ('admin', 'password');
            """
        )
        db.commit()
    return app


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = 1
    return client


def test_craigslist_jobs_page_lists_existing_scheduler_jobs(client):
    response = client.get("/control-panel/cl-jobs")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "East Texas Pets" in page
    assert "Surfboards" in page
    assert "Free Stuff" in page
    assert "Search Jobs" in page
    assert 'value="ofc"' in page
    assert 'value="rrr"' in page
    assert "https://www.craigslist.org/search/area/easttexas" in page


def test_control_panel_no_longer_contains_craigslist_search_form(client):
    response = client.get("/control-panel")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "New Craigslist Search" not in page
    assert "craigslist_query" not in page


def test_craigslist_jobs_can_be_added_and_modified(client, app):
    response = client.post(
        "/control-panel/cl-jobs",
        data={
            "action": "add",
            "name": "Kayaks",
            "term": "kayak",
            "category": "sss",
            "location_name": "Houston",
            "location_url": "https://houston.craigslist.org",
            "radius": "75",
            "run_times": "07:15, 19:45",
            "enabled": "on",
            "is_default_location": "on",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        job = db.execute(
            "SELECT id FROM craigslist_jobs WHERE job_key != 'pets' "
            "AND name = 'Kayaks'"
        ).fetchone()
        default_location = db.execute(
            "SELECT location_name, location_url FROM craigslist_jobs "
            "WHERE is_default_location = 1"
        ).fetchone()
        default_count = db.execute(
            "SELECT COUNT(*) FROM craigslist_jobs WHERE is_default_location = 1"
        ).fetchone()[0]
        db.execute(
            "UPDATE craigslist_jobs SET last_run_at = ? WHERE id = ?",
            ("2026-09-26 07:15:00", job["id"]),
        )
        db.commit()
    assert job is not None
    assert tuple(default_location) == ("Houston", "https://houston.craigslist.org")
    assert default_count == 1

    response = client.post(
        "/control-panel/cl-jobs",
        data={
            "action": "update",
            "job_id": job["id"],
            "name": "Kayaks and canoes",
            "term": "canoe",
            "category": "ofc",
            "location_name": "Austin",
            "location_url": "https://austin.craigslist.org",
            "radius": "80",
            "run_times": "06:30",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        updated = get_db().execute(
            "SELECT name, term, category, radius, run_times, location_name, "
            "location_url, enabled, is_default_location, last_run_at "
            "FROM craigslist_jobs WHERE id = ?",
            (job["id"],),
        ).fetchone()
    assert tuple(updated) == (
        "Kayaks and canoes",
        "canoe",
        "ofc",
        80,
        "06:30",
        "Austin",
        "https://austin.craigslist.org",
        0,
        0,
        "2026-09-26 07:15:00",
    )


def test_custom_craigslist_job_can_be_deleted(client, app):
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO craigslist_jobs "
            "(job_key, name, term, category, radius, run_times) "
            "VALUES ('custom-delete', 'Temporary job', 'temporary', 'sss', 100, '07:00')"
        )
        job_id = cursor.lastrowid
        db.commit()

    response = client.post(
        "/control-panel/cl-jobs",
        data={"action": "delete", "job_id": str(job_id)},
    )

    assert response.status_code == 302
    with app.app_context():
        deleted = get_db().execute(
            "SELECT id FROM craigslist_jobs WHERE id = ?", (job_id,)
        ).fetchone()
    assert deleted is None


def test_default_craigslist_job_can_be_deleted_and_default_moves(client, app):
    with app.app_context():
        job = get_db().execute(
            "SELECT id FROM craigslist_jobs WHERE job_key = 'pets'"
        ).fetchone()

    response = client.post(
        "/control-panel/cl-jobs",
        data={"action": "delete", "job_id": str(job["id"])},
    )

    assert response.status_code == 302
    with app.app_context():
        db = get_db()
        deleted = db.execute(
            "SELECT id FROM craigslist_jobs WHERE id = ?", (job["id"],)
        ).fetchone()
        new_default = db.execute(
            "SELECT job_key FROM craigslist_jobs WHERE is_default_location = 1"
        ).fetchone()
    assert deleted is None
    assert new_default["job_key"] == "surfboards"


def test_pet_job_uses_custom_term_in_category_url(monkeypatch):
    call = {}

    def fake_run_scraper(**kwargs):
        call.update(kwargs)
        return 0

    monkeypatch.setattr(craigslist_jobs, "run_scraper", fake_run_scraper)

    craigslist_jobs.execute_craigslist_job(
        {
            "term": "golden retriever",
            "category": "pet",
            "radius": 100,
        }
    )

    assert call["search_url"] == (
        "https://www.craigslist.org/search/area/easttexas"
        "?cat=pet&search_distance=100&query=golden+retriever"
    )
    assert call["max_results"] is None


def test_city_job_uses_its_own_craigslist_region(monkeypatch):
    call = {}

    def fake_run_scraper(**kwargs):
        call.update(kwargs)
        return 0

    monkeypatch.setattr(craigslist_jobs, "run_scraper", fake_run_scraper)

    craigslist_jobs.execute_craigslist_job(
        {
            "term": "surfboard",
            "category": "sss",
            "radius": 50,
            "location_name": "Houston",
            "location_url": "https://houston.craigslist.org",
        }
    )

    assert call["search_url"] == (
        "https://houston.craigslist.org/search/sss"
        "?search_distance=50&query=surfboard"
    )
    assert call["area_label"] == "Houston"


def test_job_rejects_non_craigslist_location_url(client, app):
    response = client.post(
        "/control-panel/cl-jobs",
        data={
            "action": "add",
            "name": "External location",
            "term": "item",
            "category": "sss",
            "location_name": "External",
            "location_url": "https://example.com",
            "radius": "50",
            "run_times": "08:00",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        job = get_db().execute(
            "SELECT id FROM craigslist_jobs WHERE name = 'External location'"
        ).fetchone()
    assert job is None


def test_existing_three_category_constraint_is_migrated(tmp_path):
    database_path = tmp_path / "legacy-jobs.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE craigslist_jobs (
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
        )
        connection.execute(
            "INSERT INTO craigslist_jobs "
                "(job_key, name, term, category) VALUES ('pets', 'Pets', 'pets', 'pet')"
        )

    ensure_craigslist_jobs_table(str(database_path))

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO craigslist_jobs "
            "(job_key, name, term, category) VALUES ('admin', 'Admin', 'admin', 'ofc')"
        )
        categories = connection.execute(
            "SELECT job_key, category, location_name, location_url, is_default_location "
            "FROM craigslist_jobs ORDER BY job_key"
        ).fetchall()

    assert categories == [
        ("admin", "ofc", "East Texas", "https://www.craigslist.org/search/area/easttexas", 0),
        ("free-stuff", "zip", "East Texas", "https://www.craigslist.org/search/area/easttexas", 0),
        ("pets", "pet", "East Texas", "https://www.craigslist.org/search/area/easttexas", 1),
        ("surfboards", "sss", "East Texas", "https://www.craigslist.org/search/area/easttexas", 0),
    ]


def test_scheduler_runs_jobs_at_configured_times_once(app):
    executed = []
    with app.app_context():
        db = get_db()
        six_am = datetime(2026, 9, 26, 6, 0)
        assert run_due_craigslist_jobs(
            db,
            now=six_am,
            runner=lambda job: executed.append(job["job_key"]),
        ) == 1
        assert executed == ["pets"]

        assert run_due_craigslist_jobs(
            db,
            now=six_am,
            runner=lambda job: executed.append(job["job_key"]),
        ) == 0

        eight_am = datetime(2026, 9, 26, 8, 0)
        assert run_due_craigslist_jobs(
            db,
            now=eight_am,
            runner=lambda job: executed.append(job["job_key"]),
        ) == 2
        history = db.execute(
            "SELECT status, COUNT(*) AS count FROM search_query GROUP BY status"
        ).fetchone()

    assert set(executed) == {"pets", "surfboards", "free-stuff"}
    assert history["status"] == "completed"
    assert history["count"] == 3