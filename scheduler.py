#!/usr/bin/env python3

import os
import sys
import time
from pathlib import Path
from schedule import repeat, every, run_pending

# Add ~/local/flaskr to Python path
flaskr_dir = Path(__file__).resolve().parent / "flaskr"
if str(flaskr_dir) not in sys.path:
    sys.path.append(str(flaskr_dir))

# Import application factory and task functions
from flaskr import create_app
from weather_tasks import fetch_weather, post_weather_updates_from_db, graph1
from astronomy_tasks import (
    post_apod_to_blog, 
    generate_celestial_dial, 
    post_celestial_dial_to_blog,
    fetch_astronomy_data,
    process_and_insert_astronomy_data,
    post_astronomy_data_to_blog
)

LOCATIONS_FILE = os.path.expanduser('~/local/data/locations/locations.json')
CURRENT_LOCATION = os.environ.get("CURRENT_LOCATION")

# Instantiate Flask app once for context access
app = create_app()

@repeat(every().hour)
def weather_update():
    fetch_weather()
    post_weather_updates_from_db(app, author_id=1)

@repeat(every().day.at("06:00"))
def nasa_apod():
     # 2. Post APOD
    post_apod_to_blog(app, author_id=1)    

@repeat(every().day.at("08:00"))
def daily_astronomy_update():
    # 1. Update IPGeolocation data in DB
    if not CURRENT_LOCATION:
        print("No CURRENT_LOCATION configured in environment.")
        return
    data = fetch_astronomy_data(CURRENT_LOCATION)
    if data:
        process_and_insert_astronomy_data(data)
        post_astronomy_data_to_blog(app, author_id=1)
   
    # 3. Generate and post Celestial Dial
    chart_filename = generate_celestial_dial()
    if chart_filename:
        post_celestial_dial_to_blog(app, chart_filename, author_id=1)

if __name__ == "__main__":
    # Run once immediately on startup wrapped safely
    try:
        weather_update()  # Uncomment when ready to test weather on startup
        #nasa_apod()
        #daily_astronomy_update()
    except Exception as e:
        print(f"Error during initial startup run: {e}")

    # Hand over control to schedule loop
    while True:
        run_pending()
        time.sleep(1)
