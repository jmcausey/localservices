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

# Load environment variables from .env file in project root
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# --- Constants & Configuration ---
DATABASE = os.path.expanduser('~/local/data/flaskr.sqlite')
LOCATIONS_FILE = os.path.expanduser('~/local/data/locations/locations.json')
CURRENT_LOCATION = os.environ.get("CURRENT_LOCATION")
API_KEY = os.environ.get("IPGEOLOCATION_API_KEY")  

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

def fetch_astronomy_data(location_query: str) -> Dict[str, Any]:
    """Queries ipgeolocation Astronomy API for location data."""
    lat, long = get_location_coordinates(location_query)
    if lat is None or long is None:
        print(f"Could not find coordinates for query: {location_query}")
        return {}
        
    url = f"https://api.ipgeolocation.io/astronomy?apiKey={API_KEY}&lat={lat}&long={long}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error fetching astronomy data: {e}")
        return {}

def process_and_insert_astronomy_data(api_data: Dict[str, Any]) -> bool:
    """Parses ipgeolocation API content and dynamically inserts it into SQLite."""
    if not api_data:
        return False

    valid_columns = [
        "location", "country_name", "state_prov", "city", "locality",
        "latitude", "longitude", "elevation", "mid_night", "night_end",
        "morn_astronomical_twilight_begin", "morn_astronomical_twilight_end",
        "morn_nautical_twilight_begin", "morn_nautical_twilight_end",
        "morn_civil_twilight_begin", "morn_civil_twilight_end",
        "morn_blue_hour_begin", "morn_blue_hour_end",
        "morn_golden_hour_begin", "morn_golden_hour_end", 
        "sunrise", "sunset", "eve_golden_hour_begin", "eve_golden_hour_end",
        "eve_blue_hour_begin", "eve_blue_hour_end", "eve_civil_twilight_begin",
        "eve_civil_twilight_end", "eve_nautical_twilight_begin",
        "eve_nautical_twilight_end", "eve_astronomical_twilight_begin",
        "eve_astronomical_twilight_end", "night_begin", "sun_status",
        "solar_noon", "day_length", "sun_altitude", "sun_distance",
        "sun_azimuth", "moon_phase", "moonrise", "moonset", "moon_status",
        "moon_altitude", "moon_distance", "moon_azimuth",
        "moon_parallactic_angle", "moon_illumination_percentage", "moon_angle"
    ]

    try:
        # Extract location dictionary details
        loc_info = api_data.get("location", {})
        
        # Format string location representation if loc_info is a dict
        location_str = loc_info.get("city") or loc_info.get("name") if isinstance(loc_info, dict) else str(loc_info)

        insert_payload = {
            "location": location_str,
            "country_name": loc_info.get("country_name") if isinstance(loc_info, dict) else None,
            "state_prov": loc_info.get("state_prov") if isinstance(loc_info, dict) else None,
            "city": loc_info.get("city") if isinstance(loc_info, dict) else None,
            "locality": loc_info.get("locality") if isinstance(loc_info, dict) else None,
            "latitude": loc_info.get("latitude") if isinstance(loc_info, dict) else api_data.get("latitude"),
            "longitude": loc_info.get("longitude") if isinstance(loc_info, dict) else api_data.get("longitude"),
            "elevation": loc_info.get("elevation") if isinstance(loc_info, dict) else api_data.get("elevation"),
        }

        # Map remaining root keys, ensuring no dictionary objects are passed
        for key in valid_columns:
            if key not in insert_payload:
                val = api_data.get(key)
                insert_payload[key] = None if isinstance(val, (dict, list)) else val

        # Build dynamic SQL statement
        cols = ", ".join(insert_payload.keys())
        placeholders = ", ".join([f":{k}" for k in insert_payload.keys()])
        sql = f"INSERT INTO astronomy ({cols}) VALUES ({placeholders})"

        conn = get_db_connection()
        try:
            conn.execute(sql, insert_payload)
            conn.commit()
            print(f"Successfully recorded astronomy data for {insert_payload.get('city') or CURRENT_LOCATION}.")
        finally:
            conn.close()
        return True

    except Exception as e:
        print(f"Error processing or inserting astronomy data: {e}")
        return False

def fetch_and_store_astronomy():
    """Main execution entry point."""
    if not CURRENT_LOCATION:
        print("No CURRENT_LOCATION configured in environment.")
        return

    data = fetch_astronomy_data(CURRENT_LOCATION)
    if data:
        process_and_insert_astronomy_data(data)

if __name__ == "__main__":
    fetch_and_store_astronomy()
