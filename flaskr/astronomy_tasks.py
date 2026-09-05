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
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

from flaskr.db import get_db
from flaskr.blog import create_post

# Load environment variables from .env file in project root
env_path = Path(__file__).parents[2] / ".env" if len(Path(__file__).parents) >= 3 else Path.home() / "local" / ".env"
load_dotenv(dotenv_path=env_path)

# --- Constants & Configuration ---
DATABASE = os.path.expanduser('~/local/data/flaskr.sqlite')
LOCATIONS_FILE = os.path.expanduser('~/local/data/locations/locations.json')
CURRENT_LOCATION = os.environ.get("CURRENT_LOCATION")
IPGEOLOCATION_API_KEY = os.environ.get("IPGEOLOCATION_API_KEY")
NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")
APOD_URL = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"


# --- 1. Geolocation & SQLite Database Core Helpers ---

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


# --- 2. Astronomy API Data Fetching & Dynamic Ingestion ---

def fetch_astronomy_data(location_query: str) -> Dict[str, Any]:
    """Queries ipgeolocation Astronomy API for location data."""
    if not IPGEOLOCATION_API_KEY:
        print("Error: IPGEOLOCATION_API_KEY not configured in environment.")
        return {}

    lat, long = get_location_coordinates(location_query)
    if lat is None or long is None:
        print(f"Could not find coordinates for query: {location_query}")
        return {}
        
    url = f"https://api.ipgeolocation.io/astronomy?apiKey={IPGEOLOCATION_API_KEY}&lat={lat}&long={long}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error fetching astronomy data: {e}")
        return {}


def process_and_insert_astronomy_data(api_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Parses ipgeolocation API content and dynamically inserts it into SQLite.
    If api_data is omitted, it automatically fetches data using CURRENT_LOCATION.
    """
    if api_data is None:
        if not CURRENT_LOCATION:
            print("No CURRENT_LOCATION configured in environment.")
            return False
        api_data = fetch_astronomy_data(CURRENT_LOCATION)

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
        loc_info = api_data.get("location", {})
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

        for key in valid_columns:
            if key not in insert_payload:
                val = api_data.get(key)
                insert_payload[key] = None if isinstance(val, (dict, list)) else val

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
    """Main entry point to fetch and store astronomy metrics."""
    process_and_insert_astronomy_data()


# --- 3. NASA APOD Integration ---

def fetch_apod_data() -> dict | None:
    """Fetches real-time APOD JSON payload from NASA API."""
    try:
        response = requests.get(APOD_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NASA APOD: {e}")
        return None


def post_apod_to_blog(app, author_id: int = 1) -> bool:
    """Parses APOD API response and inserts a formatted post into Flask blog."""
    apod = fetch_apod_data()
    if not apod:
        return False

    title = f"NASA APOD: {apod.get('title', 'Astronomy Picture of the Day')}"
    media_type = apod.get("media_type")
    url = apod.get("url")
    explanation = apod.get("explanation", "")
    copyright_info = apod.get("copyright", "").strip()

    if media_type == "image":
        media_html = f'<p><img src="{url}" alt="{title}" class="img-fluid rounded"></p>'
    elif media_type == "video":
        media_html = f'<div class="ratio ratio-16x9 mb-3"><iframe src="{url}" allowfullscreen></iframe></div>'
    else:
        media_html = f'<p><a href="{url}" target="_blank">View Media Content</a></p>'

    credit_html = f"<p><em>Credit: {copyright_info}</em></p>" if copyright_info else ""
    body = f"{media_html}\n{credit_html}\n<p>{explanation}</p>"

    with app.app_context():
        db = get_db()
        existing = db.execute("SELECT id FROM post WHERE title = ?", (title,)).fetchone()

        if existing:
            print(f"APOD entry '{title}' already exists in database.")
            return False

        create_post(title=title, body=body, author_id=author_id)
        print(f"Successfully published APOD post: '{title}'")
        return True


# --- 4. Celestial Dial Plot Generation & Blog Publishing ---

def fetch_latest_astronomy_data(db_path: str = DATABASE) -> dict:
    """Fetches the latest record from the astronomy table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT sunrise, sunset, solar_noon, day_length, 
               sun_altitude, sun_azimuth, sun_distance,
               moon_phase, moonrise, moonset, moon_altitude, 
               moon_illumination_percentage, timestamp
        FROM astronomy 
        ORDER BY id DESC 
        LIMIT 1
    """
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError("No records found in the 'astronomy' table.")
    return dict(row)

def time_to_rad(time_str: str | None) -> float:
    """Converts a HH:MM time string to polar radians on a 24-hour dial safely handling '-' or None."""
    if not time_str or time_str.strip() in ("-", "", "N/A"):
        return 0.0
    try:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return ((hours + minutes / 60.0) / 24.0) * 2 * np.pi
    except (ValueError, IndexError):
        return 0.0

def generate_celestial_dial(db_path: str = DATABASE, output_dir: str = "~/local/flaskr/static/media") -> str | None:
    """Generates and saves a 24-hour polar solar and lunar cycle chart directly to Flask's static media folder."""
    try:
        data = fetch_latest_astronomy_data(db_path)
    except Exception as e:
        print(f"Error fetching astronomy data for plot: {e}")
        return None

    sunrise_rad = time_to_rad(data['sunrise'])
    sunset_rad = time_to_rad(data['sunset'])
    solar_noon_rad = time_to_rad(data['solar_noon'])
    moonrise_rad = time_to_rad(data['moonrise'])
    moonset_rad = time_to_rad(data['moonset'])
    sun_azimuth_rad = np.radians(data['sun_azimuth'])

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    r_inner, r_outer = 0.72, 1.0

    # Arcs
    theta_day = np.linspace(sunrise_rad, sunset_rad, 200)
    ax.fill_between(theta_day, r_inner, r_outer, color='#FFA726', alpha=0.9, label=f"Daylight ({data['day_length']})")

    theta_night = np.linspace(sunset_rad, sunrise_rad + 2 * np.pi, 200)
    ax.fill_between(theta_night, r_inner, r_outer, color='#1A237E', alpha=0.9, label='Night')

    # Markers
    ax.plot([solar_noon_rad, solar_noon_rad], [r_inner - 0.05, r_outer + 0.05], color='#E65100', lw=2.5, linestyle='--')
    ax.plot(sunrise_rad, 0.86, 'o', color='#FFF176', markersize=10, markeredgecolor='#E65100')
    ax.plot(sunset_rad, 0.86, 'o', color='#FF7043', markersize=10, markeredgecolor='#B71C1C')
    ax.plot(moonrise_rad, 0.58, '^', color='#E0E0E0', markersize=9, markeredgecolor='#333333')
    ax.plot(moonset_rad, 0.58, 'v', color='#9E9E9E', markersize=9, markeredgecolor='#333333')
    ax.plot(sun_azimuth_rad, 1.1, '*', color='#FFD700', markersize=15, markeredgecolor='#FF6F00')

    # Clock configuration
    hours = np.arange(0, 24, 3)
    ax.set_xticks((hours / 24.0) * 2 * np.pi)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], fontsize=11, fontweight='bold')
    ax.set_yticks([])
    ax.set_ylim(0, 1.25)
    ax.grid(True, linestyle='--', alpha=0.4, color='#757575')

    summary_text = (
        "CELESTIAL DATA\n"
        "──────────────\n"
        f"Day Length: {data['day_length']}\n"
        f"Moon Phase: {data['moon_phase']}\n"
        f"Illumination: {data['moon_illumination_percentage']:.2f}%\n"
        f"Sun Altitude: {data['sun_altitude']:.2f}°\n"
        f"Sun Distance: {data['sun_distance'] / 1e6:.2f} M km\n"
        f"Moon Altitude: {data['moon_altitude']:.2f}°"
    )
    ax.text(0, 0, summary_text, ha='center', va='center', fontsize=9.5, fontweight='medium',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='#FAFAFA', edgecolor='#B0BEC5', alpha=0.95))

    plt.title("24-Hour Solar & Lunar Cycle Dial", fontsize=15, fontweight='bold', pad=25, color='#1A237E')
    plt.legend(loc='upper right', bbox_to_anchor=(1.38, 1.08), fontsize=9, framealpha=0.9)
    plt.tight_layout()

    # Save Image
    resolved_dir = os.path.expanduser(output_dir)
    os.makedirs(resolved_dir, exist_ok=True)
    filename = f"celestial_dial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = os.path.join(resolved_dir, filename)

    plt.savefig(save_path, dpi=75, bbox_inches='tight')
    plt.close('all')

    return filename


def post_celestial_dial_to_blog(app, image_name: str, author_id: int = 1) -> bool:
    """Posts the generated celestial dial chart to the Flask blog."""
    title = f"Celestial Dial: {datetime.now().strftime('%B %d, %Y')}"
    web_image_path = f"/static/media/{image_name}"
    body = (
        f'<p><img src="{web_image_path}" alt="Celestial Dial" class="img-fluid rounded"></p>'
    )

    with app.app_context():
        create_post(title=title, body=body, author_id=author_id)
        print(f"Successfully published Celestial Dial post: '{title}'")
        return True

def post_astronomy_data_to_blog(app, location_query: Optional[str] = None, author_id: int = 1) -> bool:
    """
    Fetches astronomy data, generates the 24-hour celestial dial image,
    and publishes a single blog post containing the data table on the left
    and the generated dial image on the right.
    """
    target_location = location_query or CURRENT_LOCATION
    if not target_location:
        print("Error: No location provided or configured in CURRENT_LOCATION.")
        return False

    # 1. Fetch raw API data
    data = fetch_astronomy_data(target_location)
    if not data:
        print(f"Failed to fetch astronomy data for {target_location}.")
        return False

    # 2. Store data to SQLite to ensure latest record is available for plot generator
    process_and_insert_astronomy_data(data)

    # 3. Generate the Celestial Dial Chart image file
    chart_filename = generate_celestial_dial()
    if not chart_filename:
        print("Failed to generate celestial dial image.")
        return False

    # 4. Format location and metrics
    loc_info = data.get("location", {})
    city_name = loc_info.get("city") or loc_info.get("name") if isinstance(loc_info, dict) else str(target_location)
    country = loc_info.get("country_name") if isinstance(loc_info, dict) else ""
    location_title = f"{city_name}, {country}".strip(", ") if country else city_name

    title = f"Celestial Summary: {location_title} ({datetime.now().strftime('%B %d, %Y')})"

    illumination = data.get("moon_illumination_percentage")
    illum_str = f"{float(illumination):.1f}%" if illumination is not None else "N/A"

    sun_alt = data.get("sun_altitude")
    sun_alt_str = f"{float(sun_alt):.2f}°" if sun_alt is not None else "N/A"

    moon_alt = data.get("moon_altitude")
    moon_alt_str = f"{float(moon_alt):.2f}°" if moon_alt is not None else "N/A"

    web_image_path = f"/static/media/{chart_filename}"

    # 5. Build side-by-side HTML layout (Table on Left, Dial Image on Right)
    body = f"""
    <table class="table table-sm table-borderless m-0 small align-middle w-auto">
      <tbody>
        <tr>
          <th class="p-0 text-muted pe-2 text-end">Sunrise:</th>
          <td class="p-0 font-monospace pe-3">{data.get('sunrise','N/A')}</td>
          <th class="p-0 text-muted pe-2 text-end">Moonrise:</th>
          <td class="p-0 font-monospace">{data.get('moonrise','N/A')}</td>
        </tr>
        <tr>
          <th class="p-0 text-muted pe-2 text-end">Solar Noon:</th>
          <td class="p-0 font-monospace pe-3">{data.get('solar_noon','N/A')}</td>
          <th class="p-0 text-muted pe-2 text-end">Moonset:</th>
          <td class="p-0 font-monospace">{data.get('moonset','N/A')}</td>
        </tr>
        <tr>
          <th class="p-0 text-muted pe-2 text-end">Sunset:</th>
          <td class="p-0 font-monospace pe-3">{data.get('sunset','N/A')}</td>
          <th class="p-0 text-muted pe-2 text-end">Phase:</th>
          <td class="p-0">{data.get('moon_phase','N/A')}</td>
        </tr>
        <tr>
          <th class="p-0 text-muted pe-2 text-end">Day Length:</th>
          <td class="p-0 font-monospace pe-3">{data.get('day_length','N/A')}</td>
          <th class="p-0 text-muted pe-2 text-end">Illum:</th>
          <td class="p-0 font-monospace">{illum_str}</td>
        </tr>
        <tr>
          <th class="p-0 text-muted pe-2 text-end">Sun Alt:</th>
          <td class="p-0 font-monospace pe-3">{sun_alt_str}</td>
          <th class="p-0 text-muted pe-2 text-end">Moon Alt:</th>
          <td class="p-0 font-monospace">{moon_alt_str}</td>
        </tr>
      </tbody>
    </table>
          """

    # 6. Post to Flask DB context
    with app.app_context():
        create_post(title=title, body=body, author_id=author_id)
        print(f"Successfully published Astronomy summary post: '{title}'")
        return True

if __name__ == "__main__":
    fetch_and_store_astronomy()