from datetime import datetime

import pytest

from flaskr import create_app
from flaskr.db import get_db
from flaskr.scrapers import craigslist


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "craigslist.sqlite"),
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
            INSERT INTO user (username, password) VALUES ('scraper', 'password');
            """
        )
        db.commit()
    return app


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise craigslist.requests.HTTPError()


def test_get_craigslist_listings_extracts_id_and_metadata(monkeypatch):
    posted_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    search_html = f"""
    <ul>
      <li class="cl-static-search-result">
        <a class="posting-title" href="/d/bikes/1234567890.html">Road bike</a>
        <span class="priceinfo">$1,250.00</span>
        <span class="result-hood">(Athens, TX)</span>
        <time datetime="{posted_at}"></time>
      </li>
      <li class="cl-static-search-result" data-pid="1234567890">
        <a class="posting-title" href="/d/bikes/1234567890.html">Road bike duplicate</a>
      </li>
    </ul>
    """
    detail_html = """
    <meta property="og:image" content="https://images.example/bike.jpg">
    <div id="postingbody">Well-maintained bicycle. QR Code Link to This Post</div>
    <div class="mapaddress" data-latitude="32.204" data-longitude="-95.855">
      Athens, TX
    </div>
    """
    responses = [FakeResponse(search_html), FakeResponse(detail_html)]
    requested_urls = []

    def fake_get(url, **kwargs):
        requested_urls.append(url)
        return responses.pop(0)

    monkeypatch.setattr(craigslist.requests, "get", fake_get)

    listings = craigslist.get_craigslist_listings(query="bike")

    assert len(listings) == 1
    listing = listings[0]
    assert listing["craigslist_id"] == "1234567890"
    assert listing["title"] == "Road bike"
    assert listing["price_text"] == "$1,250.00"
    assert listing["price_amount"] == 1250.0
    assert listing["location"] == "Athens, TX"
    assert listing["latitude"] == 32.204
    assert listing["longitude"] == -95.855
    assert listing["category"] == "sss"
    assert listing["search_query"] == "bike"
    assert listing["image_url"] == "https://images.example/bike.jpg"
    assert listing["description"] == "Well-maintained bicycle."
    assert len(requested_urls) == 2


def test_get_craigslist_listings_parses_current_static_craigslist_card(monkeypatch):
        search_html = """
        <li class="cl-static-search-result" title="Flame point ragdoll">
            <a href="https://www.craigslist.org/view/d/ben-wheeler-flame-point-ragdoll/4o5K7dsTZviXq1pmLfqn2C">
                <div class="title">Flame point ragdoll</div>
                <div class="details">
                    <div class="price">$0</div>
                    <div class="location">Edom</div>
                </div>
            </a>
        </li>
        """
        responses = [FakeResponse(search_html), FakeResponse("", status_code=404)]
        monkeypatch.setattr(craigslist.requests, "get", lambda *args, **kwargs: responses.pop(0))

        listings = craigslist.get_craigslist_listings(
                query="pets",
                search_url=craigslist.PET_SEARCH_URL,
                category="pet",
                area_label="East Texas",
        )

        assert len(listings) == 1
        assert listings[0]["craigslist_id"] == "4o5K7dsTZviXq1pmLfqn2C"
        assert listings[0]["title"] == "Flame point ragdoll"
        assert listings[0]["price_text"] == "$0"
        assert listings[0]["location"] == "Edom"


def test_get_craigslist_listings_skips_known_ids_before_detail_fetch(monkeypatch):
    search_html = """
    <li class="cl-static-search-result" data-pid="1234567890">
      <a class="posting-title" href="/d/bikes/1234567890.html">Road bike</a>
    </li>
    """
    requested_urls = []

    def fake_get(url, **kwargs):
        requested_urls.append(url)
        return FakeResponse(search_html)

    monkeypatch.setattr(craigslist.requests, "get", fake_get)

    listings = craigslist.get_craigslist_listings(
        query="bike",
        known_listing_ids={"1234567890"},
    )

    assert listings == []
    assert len(requested_urls) == 1


def test_get_craigslist_listings_uses_server_side_pet_search_url(monkeypatch):
    requested_urls = []

    def fake_get(url, **kwargs):
        requested_urls.append(url)
        return FakeResponse("")

    monkeypatch.setattr(craigslist.requests, "get", fake_get)

    listings = craigslist.get_craigslist_listings(
        query="pets",
        search_url=craigslist.PET_SEARCH_URL,
        category="pet",
        area_label="East Texas",
    )

    assert listings == []
    assert requested_urls == [
        "https://www.craigslist.org/search/area/easttexas?cat=pet"
    ]


def test_run_pet_scraper_uses_east_texas_pets_category(monkeypatch):
    call = {}

    def fake_run_scraper(**kwargs):
        call.update(kwargs)
        return 3

    monkeypatch.setattr(craigslist, "run_scraper", fake_run_scraper)

    assert craigslist.run_pet_scraper() == 3
    assert call == {
        "query": "pets",
        "max_results": None,
        "search_url": craigslist.PET_SEARCH_URL,
        "category": "pet",
        "area_label": "East Texas",
    }


def test_pet_search_returns_more_than_twenty_new_listings(monkeypatch):
    rows = "".join(
        (
            f'<li class="cl-static-search-result" data-pid="{listing_id}">'
            f'<a class="posting-title" href="/d/pets/{listing_id}.html">'
            f"Pet {index}</a></li>"
        )
        for index, listing_id in enumerate(range(1000000000, 1000000021))
    )
    responses = [FakeResponse(rows)]

    def fake_get(url, **kwargs):
        if "search/area/easttexas" in url:
            return responses[0]
        return FakeResponse("", status_code=404)

    monkeypatch.setattr(craigslist.requests, "get", fake_get)

    listings = craigslist.get_craigslist_listings(
        query="pets",
        max_results=None,
        search_url=craigslist.PET_SEARCH_URL,
        category="pet",
        area_label="East Texas",
    )

    assert len(listings) == 21


def test_insert_scraped_post_is_idempotent_and_links_blog_post(app):
    listing = {
        "craigslist_id": "1234567890",
        "title": "Road bike",
        "blog_title": "Bike: Road bike ($1,250)",
        "body": "Bike details",
        "price_text": "$1,250",
        "price_amount": 1250.0,
        "location": "Athens, TX",
        "latitude": 32.204,
        "longitude": -95.855,
        "listing_url": "https://easttexas.craigslist.org/d/bikes/1234567890.html",
        "category": "sss",
        "search_query": "bike",
        "posted_at": "2026-09-26 12:00:00",
        "image_url": "https://images.example/bike.jpg",
        "description": "Well-maintained bicycle.",
    }

    with app.app_context():
        db = get_db()
        assert craigslist.insert_scraped_post(listing, db=db) is True
        changed_title = {**listing, "title": "Changed title"}
        assert craigslist.insert_scraped_post(changed_title, db=db) is False

        saved_listing = db.execute(
            "SELECT craigslist_id, price_amount, location, blog_post_id "
            "FROM craigslist_postings"
        ).fetchone()
        blog_posts = db.execute("SELECT title FROM post").fetchall()

    assert tuple(saved_listing[:3]) == ("1234567890", 1250.0, "Athens, TX")
    assert saved_listing["blog_post_id"] is not None
    assert [row["title"] for row in blog_posts] == ["Bike: Road bike ($1,250)"]