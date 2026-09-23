#!/usr/bin/env python3

import os
import sys
import time
from pathlib import Path
from schedule import repeat, every, run_pending
from datetime import datetime

# Add ~/local/flaskr to Python path
flaskr_dir = Path(__file__).resolve().parent / "flaskr"
if str(flaskr_dir) not in sys.path:
    sys.path.append(str(flaskr_dir))

# Import application factory and task functions
from flaskr import create_app, get_db
from scrapers.kevinmd import run_scraper as kevinmd_scraper
from scrapers.informaticsinc import run_scraper as informaticsinc
from scrapers.cl_surfboards import run_scraper as clsurfboards
from scrapers.cl_freestuff import run_scraper as clfreestuff
from weather_tasks import (
    fetch_weather, 
    post_weather_updates_from_db, 
    graph1
    )
from astronomy_tasks import (
    post_apod_to_blog, 
    post_astronomy_data_to_blog
    )

LOCATIONS_FILE = os.path.expanduser('~/local/data/locations/locations.json')
CURRENT_LOCATION = os.environ.get("CURRENT_LOCATION")

# Instantiate Flask app once for context access
app = create_app()

@repeat(every().hour)
def weather_update():
    fetch_weather()
    
@repeat(every().day.at("08:00"))
@repeat(every().day.at("20:00"))
def daily_update():
    # Handles fetching data, DB insert, dial image generation, and single blog post
    post_astronomy_data_to_blog(app, author_id=1)
    informaticsinc()
    clfreestuff()
    clsurfboards()
    post_apod_to_blog(app, author_id=1)    

@repeat(every().minute)
def cleanup_completed_posts():
    """Removes posts marked as 'complete' from the database."""
    with app.app_context():
        db = get_db()
        cursor = db.execute("DELETE FROM post WHERE status = 'complete'")
        db.commit()
        count = cursor.rowcount
        print(f"[{datetime.now()}] Cleanup ran: removed {count} completed post(s).")

if __name__ == "__main__":    # Run once immediately on startup wrapped safely
    try:
        print('No startup jobs')
        #cleanup_completed_posts()
        #weather_update()  # Uncomment when ready to test weather on startup
        #post_apod_to_blog(app,author_id=1)
        #post_astronomy_data_to_blog(app,author_id=1)
        #post_weather_updates_from_db(app,author_id=1)
        #informaticsinc()
        #kevinmd_scraper()
        #clsurfboards()
        #clfreestuff()
    except Exception as e:
        print(f"Error during initial startup run: {e}")
    print('Starting scheduler')
    daily_update()
    while True:
        run_pending()
        time.sleep(1)
