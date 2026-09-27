import sys
import html
import re
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urldefrag, urljoin, urlparse
import requests
from bs4 import BeautifulSoup

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from flaskr import create_app
from flaskr.db import get_db

BASE_URL = "https://easttexas.craigslist.org/search/sss"
PET_SEARCH_URL = "https://www.craigslist.org/search/area/easttexas?cat=pet#search=2~list~0"


def _extract_listing_id(row, listing_url):
    listing_id = row.get("data-pid") or row.get("data-id")
    if listing_id:
        return str(listing_id)

    path = urlparse(listing_url).path
    match = re.search(r"(\d{8,})(?:\.html)?$", path)
    if match:
        return match.group(1)

    match = re.search(r"/view/d/[^/]+/([A-Za-z0-9_-]{8,})/?$", path)
    return match.group(1) if match else None


def _parse_posted_at(value):
    if not value:
        return None

    try:
        posted_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            posted_at = datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    if posted_at.tzinfo is not None:
        posted_at = posted_at.astimezone().replace(tzinfo=None)
    return posted_at


def _parse_price_amount(price_text):
    if not price_text:
        return None
    match = re.search(r"\d[\d,]*(?:\.\d{1,2})?", price_text)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_listing_description(description):
    if not description:
        return None

    description = re.sub(
        r"\bQR\s+Code\s+Link\s+to\s+This\s+Post\b",
        "",
        description,
        flags=re.IGNORECASE,
    )
    description = re.sub(r"\s+", " ", description).strip()
    return description or None


def get_craigslist_listings(
    query="surfboard",
    max_results=5,
    known_listing_ids=None,
    search_url=None,
    category=None,
    area_label="100 miles of Athens, TX",
):
    """Scrape recent Craigslist results and return their structured listing data."""
    
    if search_url:
        target_url, _ = urldefrag(search_url)
    else:
        encoded_query = quote_plus(query)
        target_url = f"{BASE_URL}?query={encoded_query}&search_distance=100&postal=75751"
    known_listing_ids = {str(value) for value in (known_listing_ids or set())}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to reach Craigslist: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []
    seen_listing_ids = set()
    now = datetime.now()

    rows = soup.select(".result-row, .cl-search-result, li.cl-static-search-result")
    
    for row in rows:
        title_el = row.select_one(".result-title, .titlestring, .title")
        listing_link = row.select_one("a.posting-title, a[href]")
        if title_el is None:
            title_el = listing_link
        price_el = row.select_one(".result-price, .price, .priceinfo")
        time_el = row.select_one("time, .result-date")
        location_el = row.select_one(".result-hood, .nearby, .location")
        
        if not title_el:
            continue

        raw_title = title_el.get_text(strip=True)
        
        # Exclude listings that contain 'modem'
        if "modem" in raw_title.lower():
            print(f"Skipping filtered item (modem): '{raw_title}'")
            continue

        post_url = urljoin(target_url, listing_link.get("href", "")) if listing_link else ""
        craigslist_id = _extract_listing_id(row, post_url)
        if not craigslist_id:
            continue
        if craigslist_id in known_listing_ids or craigslist_id in seen_listing_ids:
            continue
        seen_listing_ids.add(craigslist_id)

        # Only scrape fresh listings; the feed handles its own 24-hour visibility.
        posted_at_raw = time_el.get("datetime") if time_el else None
        posted_at = _parse_posted_at(posted_at_raw)
        if time_el:
            if posted_at and now - posted_at > timedelta(days=1):
                continue

        price_text = price_el.get_text(strip=True) if price_el else None
        display_price = price_text or "Price not listed"
        location = location_el.get_text(" ", strip=True).strip(" ()") if location_el else None

        img_url = ""
        description = None
        latitude = None
        longitude = None
        if post_url:
            try:
                detail_res = requests.get(post_url, headers=headers, timeout=10)
                if detail_res.status_code == 200:
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                    og_img = detail_soup.select_one('meta[property="og:image"]')
                    if og_img and og_img.get("content"):
                        img_url = og_img.get("content")
                    posting_body = detail_soup.select_one("#postingbody, .postingbody")
                    description_meta = detail_soup.select_one(
                        'meta[property="og:description"], meta[name="description"]'
                    )
                    if posting_body:
                        description = posting_body.get_text(" ", strip=True)
                    elif description_meta:
                        description = description_meta.get("content", "").strip() or None
                    description = _clean_listing_description(description)

                    map_address = detail_soup.select_one(".mapaddress")
                    if map_address:
                        location = location or map_address.get_text(" ", strip=True) or None
                        latitude = _as_float(map_address.get("data-latitude"))
                        longitude = _as_float(map_address.get("data-longitude"))
            except requests.RequestException:
                pass

        blog_title = f"{query.capitalize()}: {raw_title} ({display_price})"
        body_parts = [
            f"<strong>Price:</strong> {html.escape(display_price)}",
            f"<br><strong>Location:</strong> {html.escape(location or 'Not listed')}",
            f"<br>Found on Craigslist ({html.escape(area_label)}).",
        ]

        if description:
            body_parts.append(f"<br><br>{html.escape(description)}")
        if img_url:
            body_parts.append(
                f"<br><br><img src='{html.escape(img_url, quote=True)}' "
                f"alt='{html.escape(raw_title, quote=True)}' "
                "style='max-width:100%; height:auto; border-radius:4px;'>"
            )
        body_parts.append(
            f"<br><br><a href='{html.escape(post_url, quote=True)}' "
            "target='_blank' rel='noopener noreferrer'>View Craigslist Listing</a>"
        )

        listings.append({
            "craigslist_id": craigslist_id,
            "title": raw_title,
            "blog_title": blog_title,
            "body": "".join(body_parts),
            "price_text": price_text,
            "price_amount": _parse_price_amount(price_text),
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "listing_url": post_url,
            "category": category or urlparse(target_url).path.rstrip("/").rsplit("/", 1)[-1],
            "search_query": query,
            "posted_at": posted_at.isoformat(sep=" ") if posted_at else posted_at_raw,
            "image_url": img_url or None,
            "description": description,
        })

        if max_results is not None and len(listings) >= max_results:
            break

    return listings

def insert_scraped_post(listing, author_id=1, status="new", db=None):
    """Store a Craigslist listing once and create its corresponding blog post."""
    if db is None:
        app = create_app()
        with app.app_context():
            return insert_scraped_post(listing, author_id, status, get_db())

    cursor = db.execute(
        """
        INSERT OR IGNORE INTO craigslist_postings (
            craigslist_id, title, price_text, price_amount, location, latitude,
            longitude, listing_url, category, search_query, posted_at, image_url,
            description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            listing["craigslist_id"],
            listing["title"],
            listing.get("price_text"),
            listing.get("price_amount"),
            listing.get("location"),
            listing.get("latitude"),
            listing.get("longitude"),
            listing["listing_url"],
            listing.get("category"),
            listing.get("search_query"),
            listing.get("posted_at"),
            listing.get("image_url"),
            listing.get("description"),
        ),
    )
    if cursor.rowcount == 0:
        return False

    blog_cursor = db.execute(
        "INSERT INTO post (author_id, title, body, status) VALUES (?, ?, ?, ?)",
        (author_id, listing.get("blog_title", listing["title"]), listing["body"], status),
    )
    db.execute(
        "UPDATE craigslist_postings SET blog_post_id = ? WHERE id = ?",
        (blog_cursor.lastrowid, cursor.lastrowid),
    )
    db.commit()
    return True

def run_scraper(
    query="surfboard",
    max_results=5,
    search_url=None,
    category=None,
    area_label="100 miles of Athens, TX",
):
    print(f"Scraping recent Craigslist listings for '{query}' in {area_label}...")
    app = create_app()
    with app.app_context():
        db = get_db()
        known_ids = {
            row["craigslist_id"]
            for row in db.execute("SELECT craigslist_id FROM craigslist_postings")
        }
        listings = get_craigslist_listings(
            query=query,
            max_results=max_results,
            known_listing_ids=known_ids,
            search_url=search_url,
            category=category,
            area_label=area_label,
        )
        inserted = sum(insert_scraped_post(item, db=db) for item in listings)
        print(f"Stored {inserted} new Craigslist listings.")
        return inserted


def run_pet_scraper():
    """Scrape new East Texas community/pets listings for the daily job."""
    return run_scraper(
        query="pets",
        max_results=None,
        search_url=PET_SEARCH_URL,
        category="pet",
        area_label="East Texas",
    )

if __name__ == "__main__":
    # Accepts an optional command-line argument for the search query (e.g. `python script.py kayak`)
    search_term = sys.argv[1] if len(sys.argv) > 1 else "surfboard"
    run_scraper(query=search_term)