import pytest

from flaskr import create_app
from flaskr.db import get_db
from flaskr import blog


@pytest.fixture
def app(tmp_path):
	app = create_app({
		"TESTING": True,
		"DATABASE": str(tmp_path / "test.sqlite"),
	})

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
			INSERT INTO user (username, password) VALUES ('author', 'password');
			INSERT INTO user (username, password) VALUES ('other', 'password');
			"""
		)
		db.commit()

	yield app


@pytest.fixture
def client(app):
	return app.test_client()


def _insert_post(
	app,
	title="Test post",
	body="Test body",
	status="new",
	created="2026-01-01 12:00:00",
	author_id=1,
):
	with app.app_context():
		db = get_db()
		cursor = db.execute(
			"INSERT INTO post (author_id, created, title, body, status) "
			"VALUES (?, ?, ?, ?, ?)",
			(author_id, created, title, body, status),
		)
		db.commit()
		return cursor.lastrowid


def _insert_post_relative_to_now(app, title, status, age):
	with app.app_context():
		db = get_db()
		cursor = db.execute(
			"INSERT INTO post (author_id, created, title, body, status) "
			"VALUES (1, datetime('now', ?), ?, 'Test body', ?)",
			(age, title, status),
		)
		db.commit()
		return cursor.lastrowid


def _link_craigslist_listing(app, post_id, craigslist_id, category="pet"):
	with app.app_context():
		get_db().execute(
			"INSERT INTO craigslist_postings "
			"(craigslist_id, title, listing_url, category, blog_post_id) "
			"VALUES (?, ?, ?, ?, ?)",
			(
				craigslist_id,
				"Craigslist listing",
				f"https://craigslist.test/{craigslist_id}",
				category,
				post_id,
			),
		)
		get_db().commit()


def _log_in(client, user_id=1):
	with client.session_transaction() as session:
		session["user_id"] = user_id


def test_latest_post_id_is_zero_when_there_are_no_posts(client):
	response = client.get("/api/latest-post-id")

	assert response.status_code == 200
	assert response.json == {"latest_id": 0}


def test_latest_post_id_returns_most_recent_post(client, app):
	_insert_post_relative_to_now(app, "Older", "new", "-2 hours")
	newest_post_id = _insert_post_relative_to_now(app, "Newer", "new", "-1 hour")

	response = client.get("/api/latest-post-id")

	assert response.status_code == 200
	assert response.json == {"latest_id": newest_post_id}


def test_latest_post_id_is_scoped_to_the_active_feed(client, app):
	blog_post_id = _insert_post_relative_to_now(
		app, "Regular feed post", "new", "-2 minutes"
	)
	pet_post_id = _insert_post_relative_to_now(
		app, "Pet feed post", "new", "-1 minute"
	)
	_link_craigslist_listing(app, pet_post_id, "pet-feed-1")

	blog_response = client.get("/api/latest-post-id?feed=blog")
	cl_response = client.get("/api/latest-post-id?feed=cl")
	pets_response = client.get("/api/latest-post-id?feed=pets")

	assert blog_response.json == {"latest_id": blog_post_id}
	assert cl_response.json == {"latest_id": pet_post_id}
	assert pets_response.json == {"latest_id": pet_post_id}


def test_blog_feed_expires_posts_but_keeps_pending_and_hides_complete(client, app):
	_insert_post_relative_to_now(app, "Recent new", "new", "-2 hours")
	_insert_post_relative_to_now(app, "Expired new", "new", "-2 days")
	_insert_post_relative_to_now(app, "Expired pending", "pending", "-2 days")
	_insert_post_relative_to_now(app, "Recent complete", "complete", "-2 hours")
	_insert_post_relative_to_now(app, "Expired complete", "complete", "-2 days")

	response = client.get("/")
	page = response.get_data(as_text=True)

	assert response.status_code == 200
	assert "Recent new" in page
	assert "Expired pending" in page
	assert "Expired new" not in page
	assert "Recent complete" not in page
	assert "Expired complete" not in page


def test_cl_pets_route_separates_pet_posts_from_general_blog(client, app):
	regular_post_id = _insert_post_relative_to_now(
		app, "Regular blog post", "new", "-2 hours"
	)
	pet_post_id = _insert_post_relative_to_now(
		app, "Recent pet listing", "new", "-2 hours"
	)
	pending_pet_id = _insert_post_relative_to_now(
		app, "Old pending pet listing", "pending", "-2 days"
	)
	complete_pet_id = _insert_post(app, title="Complete pet listing", status="complete")
	other_cl_post_id = _insert_post_relative_to_now(
		app, "Surfboard Craigslist listing", "new", "-2 hours"
	)
	legacy_cl_post_id = _insert_post_relative_to_now(
		app, "Free: Legacy listing", "new", "-2 hours"
	)
	_link_craigslist_listing(app, pet_post_id, "pet-1001")
	_link_craigslist_listing(app, pending_pet_id, "pet-1002")
	_link_craigslist_listing(app, complete_pet_id, "pet-1003")
	_link_craigslist_listing(app, other_cl_post_id, "listing-2001", category="sss")
	with app.app_context():
		get_db().execute(
			"UPDATE post SET body = ? WHERE id = ?",
			(
				'<a href="https://craigslist.test/legacy">'
				"View Craigslist Listing</a>",
				legacy_cl_post_id,
			),
		)
		get_db().commit()

	general_page = client.get("/").get_data(as_text=True)
	cl_response = client.get("/cl")
	cl_page = cl_response.get_data(as_text=True)
	pets_response = client.get("/cl-pets")
	pets_page = pets_response.get_data(as_text=True)

	assert cl_response.status_code == 200
	assert "Craigslist Listings" in cl_page
	assert "Recent pet listing" in cl_page
	assert "Surfboard Craigslist listing" in cl_page
	assert "Free: Legacy listing" in cl_page
	assert "Regular blog post" not in cl_page
	assert pets_response.status_code == 200
	assert "Craigslist Pets" in pets_page
	assert '<a href="/cl">CL</a>' in pets_page
	assert '<a href="/cl">All</a>' in pets_page
	assert '<a href="/cl-pets">Pets</a>' in pets_page
	assert cl_page.index('>CL</a>') < cl_page.index('>All</a>')
	assert "Regular blog post" in general_page
	assert "Recent pet listing" not in general_page
	assert "Surfboard Craigslist listing" not in general_page
	assert "Free: Legacy listing" not in general_page
	assert "Recent pet listing" in pets_page
	assert "Old pending pet listing" in pets_page
	assert "Complete pet listing" not in pets_page


def test_audio_endpoint_sanitizes_html_and_returns_audio(client, app, monkeypatch):
	post_id = _insert_post(
		app,
		title="<b>Morning</b>",
		body="<p>Hello <em>world</em>.</p>",
	)
	spoken_text = []

	class FakeTTS:
		def __init__(self, text, lang):
			spoken_text.append((text, lang))

		def write_to_fp(self, file_object):
			file_object.write(b"fake-mp3-data")

	monkeypatch.setattr(blog, "gTTS", FakeTTS)

	response = client.get(f"/audio/{post_id}")

	assert response.status_code == 200
	assert response.mimetype == "audio/mpeg"
	assert response.data == b"fake-mp3-data"
	assert spoken_text == [("Morning. Hello world.", "en")]


def test_audio_endpoint_returns_404_for_missing_post(client):
	response = client.get("/audio/999")

	assert response.status_code == 404
	assert response.get_data(as_text=True) == "Post not found"


def test_create_redirects_to_login_for_anonymous_user(client):
	response = client.post("/create", data={"title": "New", "body": "Body"})

	assert response.status_code == 302
	assert response.headers["Location"].endswith("/auth/login")


def test_create_saves_post_for_logged_in_user(client, app):
	_log_in(client)

	response = client.post(
		"/create",
		data={"title": "New post", "body": "Post body", "status": "PENDING"},
	)

	assert response.status_code == 302
	with app.app_context():
		post = get_db().execute(
			"SELECT title, body, status, author_id FROM post"
		).fetchone()
	assert tuple(post) == ("New post", "Post body", "pending", 1)


def test_status_route_normalizes_completed_to_complete(client, app):
	post_id = _insert_post(app)
	_log_in(client)

	response = client.post(f"/{post_id}/status/completed")

	assert response.status_code == 302
	with app.app_context():
		post = get_db().execute(
			"SELECT status FROM post WHERE id = ?", (post_id,)
		).fetchone()
	assert post["status"] == "complete"


def test_status_change_returns_to_originating_craigslist_feed(client, app):
	post_id = _insert_post_relative_to_now(
		app, "Recent craigslist listing", "new", "-1 hour"
	)
	with app.app_context():
		_link_craigslist_listing(app, post_id, "status-redirect-1")
	_log_in(client)

	response = client.post(
		f"/{post_id}/status/complete",
		data={"return_to": "/cl"},
	)

	assert response.status_code == 302
	assert response.headers["Location"].endswith("/cl")


def test_status_change_rejects_external_return_url(client, app):
	post_id = _insert_post_relative_to_now(
		app, "Recent post", "new", "-1 hour"
	)
	_log_in(client)

	response = client.post(
		f"/{post_id}/status/pending",
		data={"return_to": "https://example.com"},
	)

	assert response.status_code == 302
	assert response.headers["Location"].endswith("/")


def test_user_cannot_change_another_users_post_status(client, app):
	post_id = _insert_post(app)
	_log_in(client, user_id=2)

	response = client.post(f"/{post_id}/status/complete")

	assert response.status_code == 403
