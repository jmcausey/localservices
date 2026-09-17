import sys
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Ensure project root is in path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from flaskr import create_app
from flaskr.db import get_db

TARGET_URL = "https://www.kevinmd.com/category/tech"

def get_latest_kevinmd_blog():
    """Scrapes the latest tech article title and content from KevinMD."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to reach KevinMD Tech category: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Target article titles and links on WordPress-based layout
    title_el = None
    post_url = ""

    for selector in [".entry-title a", "article a.entry-title-link", "h2.entry-title a", "h3 a"]:
        elements = soup.select(selector)
        for el in elements:
            href = el.get("href", "")
            text = el.get_text(strip=True)
            if href and len(text) > 5:
                title_el = el
                post_url = href
                break
        if title_el:
            break

    if not title_el:
        print("Could not locate blog elements on KevinMD page.")
        return None

    title = title_el.get_text(strip=True)

    if not post_url.startswith("http"):
        post_url = "https://www.kevinmd.com" + post_url

    # Fetch full article body
    body_text = f"Scraped from KevinMD Tech. Read full article at: <a href='{post_url}' target='_blank'>"
    try:
        detail_res = requests.get(post_url, headers=headers, timeout=10)
        if detail_res.status_code == 200:
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")
            content_area = detail_soup.select_one(".entry-content, article, .post-content")
            if content_area:
                paragraphs = [p.get_text(strip=True) for p in content_area.find_all("p") if len(p.get_text(strip=True)) > 20]
                if paragraphs:
                    body_text = "\n\n".join(paragraphs[:4]) + f"<br><br><a href='{post_url}' target='_blank'>Read full article on KevinMD</a>"
    except requests.RequestException:
        pass

    return {
        "title": f"KevinMD Tech: {title}",
        "body": body_text
    }

def insert_scraped_post(title, body, author_id=1, status="new"):
    """Inserts the blog post into Flaskr database if it doesn't already exist."""
    app = create_app()
    with app.app_context():
        db = get_db()
        
        existing = db.execute(
            "SELECT id FROM post WHERE title = ?", (title,)
        ).fetchone()

        if existing:
            print(f"Skipping: Post '{title}' already exists in DB.")
            return False

        db.execute(
            "INSERT INTO post (author_id, title, body, status) VALUES (?, ?, ?, ?)",
            (author_id, title, body, status)
        )
        db.commit()
        print(f"Successfully posted: '{title}' to Flaskr blog!")
        return True

def run_scraper():
    print("Scraping latest tech article from KevinMD...")
    blog_data = get_latest_kevinmd_blog()
    if blog_data:
        insert_scraped_post(blog_data["title"], blog_data["body"])

if __name__ == "__main__":
    run_scraper()