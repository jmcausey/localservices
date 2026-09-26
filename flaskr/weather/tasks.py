#!/usr/bin/env python3

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv

from flaskr.db import get_db
from flaskr.blog import create_post

# Load environment variables from .env file in project root
env_path = Path.home() / "local" / ".env"
load_dotenv(dotenv_path=env_path)

# --- Constants & Configuration ---
DATABASE = os.path.expanduser('~/local/data/flaskr.sqlite')
LOCATIONS_FILE = os.path.expanduser('~/local/data/locations/locations.json')
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
CURRENT_LOCATION = os.environ.get("CURRENT_LOCATION")
OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_UNITS = "imperial"


def load_locations() -> Dict[str, Tuple[float, float]]:
    """Loads location coordinates mapping from JSON configuration."""
    try:
        with open(LOCATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load locations file: {e}")
        return {}


def get_location_coordinates(location_query: str) -> Tuple[Optional[float], Optional[float]]:
    """Looks up geolocation metrics for a specific city query string."""
    locations_map = load_locations()
    for name, coords in locations_map.items():
        if location_query.lower() in name.lower():
            return coords[0], coords[1]
    return None, None


def get_db_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection instance to the SQLite database."""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_weather_data_from_api(city_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Fetches real-time JSON weather data using the OpenWeather API."""
    if not city_name:
        print("Error: CURRENT_LOCATION is not defined in environment.")
        return None

    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "something":
        print("Error: OPENWEATHER_API_KEY not set properly.")
        return None

    lat, lon = get_location_coordinates(city_name)
    if lat is None or lon is None:
        print(f"Coordinates for '{city_name}' could not be matched in {LOCATIONS_FILE}.")
        return None

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": OPENWEATHER_UNITS
    }

    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None


def process_and_insert_weather_data(api_data: Dict[str, Any]) -> bool:
    """Parses raw API contents safely and pipes them directly into SQLite."""
    if not api_data:
        return False

    try:
        coord = api_data.get("coord", {})
        weather_list = api_data.get("weather", [{}])
        main_metrics = api_data.get("main", {})
        wind = api_data.get("wind", {})
        sys_data = api_data.get("sys", {})

        geolocation = f"{coord['lat']},{coord['lon']}" if "lat" in coord and "lon" in coord else None

        sunrise_val = None
        if "sunrise" in sys_data:
            sunrise_val = datetime.fromtimestamp(sys_data["sunrise"]).strftime('%Y-%m-%d %H:%M:%S')

        sunset_val = None
        if "sunset" in sys_data:
            sunset_val = datetime.fromtimestamp(sys_data["sunset"]).strftime('%Y-%m-%d %H:%M:%S')

        insert_data = {
            "location": api_data.get("name"),
            "geolocation": geolocation,
            "description": weather_list[0].get("description") if weather_list else None,
            "temperature": main_metrics.get("temp"),
            "pressure": main_metrics.get("pressure"),
            "feelslike": main_metrics.get("feels_like"),
            "humidity": main_metrics.get("humidity"),
            "visibility": api_data.get("visibility"),
            "windspeed": wind.get("speed"),
            "winddirection": wind.get("deg"),
            "clouds": api_data.get("clouds", {}).get("all"),
            "sunrise": sunrise_val,
            "sunset": sunset_val
        }

        conn = get_db_connection()
        try:
            conn.execute(
                '''INSERT INTO chart (
                    location, geolocation, description, temperature, pressure,
                    feelslike, humidity, visibility, windspeed, winddirection,
                    clouds, sunrise, sunset
                ) VALUES (
                    :location, :geolocation, :description, :temperature, :pressure,
                    :feelslike, :humidity, :visibility, :windspeed, :winddirection,
                    :clouds, :sunrise, :sunset
                )''',
                insert_data
            )
            conn.commit()
            print(f"Successfully recorded weather for {insert_data['location']}.")
        finally:
            conn.close()
        return True

    except Exception as e:
        print(f"Error processing or inserting data: {e}")
        return False


def graph1(db_path=DATABASE, location_name=CURRENT_LOCATION, output_filename=None):
    """Generates a stacked time-series plot of temperature vs humidity."""
    if not output_filename:
        output_dir = os.path.expanduser('~/local/data/graphs')
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"mpl_stackplot_{int(time.time())}.png")

    conn = sqlite3.connect(db_path)
    query = """
        SELECT created_at, temperature, humidity 
        FROM chart 
        WHERE location = ? 
        ORDER BY created_at ASC
    """
    df = pd.read_sql_query(query, conn, params=(location_name,))
    conn.close()

    if df.empty:
        print(f"No data found for location: {location_name}")
        return None

    plt.style.use('_mpl-gallery')
    df["created_at"] = pd.to_datetime(df["created_at"])
    df.set_index("created_at", inplace=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.stackplot(
        df.index, 
        df["temperature"], 
        df["humidity"], 
        labels=["Temperature", "Humidity (%)"],
        colors=["tab:red", "tab:blue"],
        alpha=0.6
    )

    ax.set_xlabel("Time (Hourly)", fontsize=12)
    ax.set_ylabel("Stacked Values", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.4)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.legend(loc="upper left")
    plt.title(f"Hourly Weather Stackplot - {location_name}", fontsize=14, fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close(fig)
    
    return os.path.basename(output_filename)


def post_weather_updates_from_db(app, author_id=1):
    """
    Reads weather logs from the DB and creates a new weather blog post.
    Must run within Flask app context.
    """
    with app.app_context():
        db = get_db()
        
        # 1. Fetch hourly weather data from your database
        weather_rows = db.execute(
            'SELECT location, created_at, temperature, pressure, feelslike, windspeed, winddirection, dew_point, description, humidity '
            'FROM chart '
            'ORDER BY created_at DESC LIMIT 1'
        ).fetchall()

        if not weather_rows:
            print("No weather data found in DB.")
            return
        location = weather_rows[0]['location']

        # 2. Format rows into your styled HTML .table markup
        table_rows = "".join(
            f"\n"
            f"{row['description']} | "
            f"temperature: {row['temperature']}°F | "
            f"feels like: {row['feelslike']} | "
            f"humidity: {row['humidity']}% | "
            f"windspead: {row['windspeed']} | "
            f"winddirection: {row['winddirection']} | "
            f"dew_point: {row['dew_point']} "
            for row in weather_rows
        )

        # 3. Access blog creation API logic directly
        title = f"{location} weather - {datetime.now().strftime('%I:%M %p')}"
        body = f"{table_rows}"

        create_post(title=title, body=body, author_id=author_id)
        print(f"Successfully posted: '{title}'")


def fetch_weather():
    """Main execution target for scheduler."""
    data = get_weather_data_from_api(CURRENT_LOCATION)
    if data:
        process_and_insert_weather_data(data)


if __name__ == "__main__":
    # Standard standalone run (API fetch + chart generation)
    fetch_weather()
    graph1()
    
    # Optional blog update (requires Flask application context)
    from flaskr import create_app
    app = create_app()
    post_weather_updates_from_db(app, author_id=1)