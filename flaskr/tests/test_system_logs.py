import pytest

from flaskr import create_app
from flaskr.db import get_db


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "system-logs.sqlite"),
        }
    )
    with app.app_context():
        db = get_db()
        db.execute(
            "CREATE TABLE user ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)"
        )
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("log-viewer", "password"),
        )
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _log_in(client):
    with client.session_transaction() as session:
        session["user_id"] = 1


def test_system_logs_are_persisted_and_filterable(client, app):
    with app.app_context():
        app.logger.warning("scheduled task delayed")
        app.logger.error("database connection failed")
    _log_in(client)

    response = client.get("/control-panel/system-logs?level=ERROR")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "database connection failed" in page
    assert "scheduled task delayed" not in page


def test_system_logs_page_requires_login(client):
    response = client.get("/control-panel/system-logs")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")