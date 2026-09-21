import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from flaskr import create_app
from flaskr.db import get_db

BASE_URL = "https://easttexas.craigslist.org/search/sss"

def get_craigslist_listings(query="surfboard", max_results=5):
    """Scrapes listings from Craigslist near Athens, TX based on a search term, 
    filtering out modems, posts older than 1 day, and internal duplicates."""
    
    encoded_query = quote_plus(query)
    target_url = f"{BASE_URL}?query={encoded_query}&search_distance=100&postal=75751"

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
    seen_titles = set()
    now = datetime.now()

    rows = soup.select(".result-row, .cl-search-result, li.cl-static-search-result")
    
    for row in rows:
        title_el = row.select_one(".result-title, .titlestring, a.posting-title, a")
        price_el = row.select_one(".result-price, .price")
        time_el = row.select_one("time, .result-date")
        
        if not title_el:
            continue

        raw_title = title_el.get_text(strip=True)
        
        # Exclude listings that contain 'modem'
        if "modem" in raw_title.lower():
            print(f"Skipping filtered item (modem): '{raw_title}'")
            continue

        # Check post age (must be within the last 24 hours)
        if time_el:
            dt_str = time_el.get("datetime")
            if dt_str:
                try:
                    post_time = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M")
                    if now - post_time > timedelta(days=1):
                        print(f"Skipping old listing (> 1 day): '{raw_title}' ({dt_str})")
                        continue
                except ValueError:
                    pass

        post_url = title_el.get("href", "")
        price = price_el.get_text(strip=True) if price_el else "Price not listed"

        if post_url and not post_url.startswith("http"):
            post_url = "https://dallas.craigslist.org" + post_url

        formatted_title = f"{query.capitalize()}: {raw_title} ({price})"

        # Deduplicate in-memory if the scraper encounters duplicate items in the current page batch
        if formatted_title in seen_titles:
            continue
        seen_titles.add(formatted_title)

        # Fetch High-Res image from metadata
        img_url = ""
        if post_url:
            try:
                detail_res = requests.get(post_url, headers=headers, timeout=10)
                if detail_res.status_code == 200:
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                    og_img = detail_soup.select_one('meta[property="og:image"]')
                    if og_img and og_img.get("content"):
                        img_url = og_img.get("content")
            except requests.RequestException:
                pass

        # Build formatted HTML body
        body_parts = [
            f"<strong>Price:</strong> {price}",
            f"<br>Found on Craigslist (100 miles of Athens, TX)."
        ]
        
        if img_url:
            body_parts.append(f"<br><br><img src='{img_url}' alt='{raw_title}' style='max-width:100%; height:auto; border-radius:4px;'>")
            
        body_parts.append(f"<br><br><a href='{post_url}' target='_blank'>View Craigslist Listing</a>")
        
        listings.append({
            "title": formatted_title,
            "body": "".join(body_parts)
        })
        
        if len(listings) >= max_results:
            break

    return listings

def insert_scraped_post(title, body, author_id=1, status="new"):
    """Inserts the listing into Flaskr database if it doesn't already exist."""
    app = create_app()
    with app.app_context():
        db = get_db()
        
        # Database-level deduplication check by title
        existing = db.execute(
            "SELECT id FROM post WHERE title = ?", (title,)
        ).fetchone()

        if existing:
            print(f"Skipping duplicate database record: '{title}'")
            return False

        db.execute(
            "INSERT INTO post (author_id, title, body, status) VALUES (?, ?, ?, ?)",
            (author_id, title, body, status)
        )
        db.commit()
        print(f"Successfully posted recent Craigslist find: '{title}'")
        return True

def run_scraper(query="surfboard"):
    print(f"Scraping recent Craigslist listings for '{query}' near Athens, TX...")
    listings = get_craigslist_listings(query=query)
    for item in listings:
        insert_scraped_post(item["title"], item["body"])

if __name__ == "__main__":
    # Accepts an optional command-line argument for the search query (e.g. `python script.py kayak`)
    search_term = sys.argv[1] if len(sys.argv) > 1 else "surfboard"
    run_scraper(query=search_term)