import sys
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Ensure project root is in path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from flaskr import create_app
from flaskr.db import get_db

TARGET_URL = "https://www.informaticsinc.com/blog"

def get_latest_remote_blog():
    """Scrapes the latest blog post title and content from Informatics Inc."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to reach Informatics blog: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Broader selector sequence to target article link and title
    title_el = None
    post_url = ""

    # Try matching common card, listing, or header anchor tags
    for selector in [".blog-index__item a", ".card a", "article a", "main a[href*='/blog/']", "h2 a", "h3 a"]:
        elements = soup.select(selector)
        for el in elements:
            href = el.get("href", "")
            text = el.get_text(strip=True)
            # Ensure it's a blog post link and not a top-level nav item
            if href and "/blog/" in href and href.rstrip('/') != "/blog" and len(text) > 5:
                title_el = el
                post_url = href
                break
        if title_el:
            break

    if not title_el:
        print("Could not locate blog elements on page. Check network access or HTML layout.")
        return None

    title = title_el.get_text(strip=True)

    if not post_url.startswith("http"):
        post_url = "https://www.informaticsinc.com" + post_url

    # Fetch detail page content
    body_text = f"Scraped from Informatics Inc. Read full article at: {post_url}"
    try:
        detail_res = requests.get(post_url, headers=headers, timeout=10)
        if detail_res.status_code == 200:
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")
            # Pull body text from article tags or main wrapper
            content_area = detail_soup.select_one("article, main, .blog-detail, .content")
            if content_area:
                paragraphs = [p.get_text(strip=True) for p in content_area.find_all("p") if len(p.get_text(strip=True)) > 20]
                if paragraphs:
                    body_text = "\n\n".join(paragraphs[:4]) + f"\n\n[Read full article on Informatics Inc.]({post_url})"
    except requests.RequestException:
        pass

    return {
        "title": f"Informatics: {title}",
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
    print("Scraping latest blog post from Informatics Inc...")
    blog_data = get_latest_remote_blog()
    if blog_data:
        insert_scraped_post(blog_data["title"], blog_data["body"])

if __name__ == "__main__":
    run_scraper()