import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from flaskr import create_app
from flaskr.db import get_db

# East Texas Craigslist Free Stuff category URL (`cat=zip`)
TARGET_URL = "https://easttexas.craigslist.org/search/zip"

def get_craigslist_free_stuff():
    """Scrapes free stuff listings from East Texas Craigslist, filtering out modems and posts older than 1 day."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to reach Craigslist: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []
    now = datetime.now()

    rows = soup.select(".result-row, .cl-search-result, li.cl-static-search-result")
    
    for row in rows:
        title_el = row.select_one(".result-title, .titlestring, a.posting-title, a")
        price_el = row.select_one(".result-price, .price")
        time_el = row.select_one("time, .result-date")
        
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        

        # Check post age (must be within the last 24 hours)
        if time_el:
            dt_str = time_el.get("datetime")
            if dt_str:
                try:
                    post_time = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M")
                    if now - post_time > timedelta(days=1):
                        print(f"Skipping old listing (> 1 day): '{title}' ({dt_str})")
                        continue
                except ValueError:
                    pass

        post_url = title_el.get("href", "")
        price = "Free"

        if post_url and not post_url.startswith("http"):
            post_url = "https://easttexas.craigslist.org" + post_url

        # Visit the individual posting page to grab the high-res image via OpenGraph meta tag
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

        # Build formatted body with picture and price
        body_parts = [
            f"<strong>Price:</strong> {price}",
            f"<br>Found in Free Stuff on East Texas Craigslist."
        ]
        
        if img_url:
            body_parts.append(f"<br><br><img src='{img_url}' alt='{title}' style='max-width:100%; height:auto; border-radius:4px;'>")
            
        body_parts.append(f"<br><br><a href='{post_url}' target='_blank'>View Craigslist Listing</a>")
        
        listings.append({
            "title": f"Free: {title}",
            "body": "".join(body_parts)
        })
        
        # Limit to top 5 recent valid listings per run
        if len(listings) >= 5:
            break

    return listings

def insert_scraped_post(title, body, author_id=1, status="new"):
    """Inserts the listing into Flaskr database if it doesn't already exist."""
    app = create_app()
    with app.app_context():
        db = get_db()
        
        existing = db.execute(
            "SELECT id FROM post WHERE title = ?", (title,)
        ).fetchone()

        if existing:
            return False

        db.execute(
            "INSERT INTO post (author_id, title, body, status) VALUES (?, ?, ?, ?)",
            (author_id, title, body, status)
        )
        db.commit()
        print(f"Successfully posted recent East Texas free find: '{title}'")
        return True

def run_scraper():
    print("Scraping recent free stuff on East Texas Craigslist...")
    listings = get_craigslist_free_stuff()
    for item in listings:
        insert_scraped_post(item["title"], item["body"])

if __name__ == "__main__":
    run_scraper()