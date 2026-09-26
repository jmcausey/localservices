import os
import json
import socket
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, jsonify, render_template, request, current_app
from flaskr.db import get_db
from flaskr.blog import create_post

bp = Blueprint('weather', __name__)
hostname = socket.gethostname()

LOCATIONS_FILE = "/home/jon/local/data/locations/locations.json"

def format_time(ts):
    if not ts:
        return None
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%A %I:%M:%S %p")

def load_locations() -> Dict[str, Tuple[float, float]]:
    """Loads location coordinates mapping from the JSON configuration."""
    try:
        with open(LOCATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Uses current_app to safely access the app context log from inside a Blueprint
        current_app.logger.error(f"Failed to load locations file: {e}")
        return {}

def get_location_coordinates(location_query: str) -> Tuple[Optional[float], Optional[float]]:
    """Looks up geolocation metrics for a specific city query string."""
    locations_map = load_locations()
    for name, coords in locations_map.items():
        if location_query.lower() in name.lower():
            return coords[0], coords[1]
    return None, None


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

@bp.route('/')
@bp.route('/weather')
def weather():
    selected_city = request.args.get('city', '').strip()
    current_location = os.environ.get("CURRENT_LOCATION")
    db = get_db()

    # Shared base query fields
    base_query = """
        SELECT 
            created_at AS Time, 
            location AS Location,  
            description AS Description,  
            temperature AS [Temperature (°C)],  
            pressure AS Barometer,  
            feelslike AS [Feels Like],  
            humidity AS Humidity,  
            dew_point AS [Dew Point],  
            winddirection AS [Wind Direction],  
            windspeed AS [Wind Speed],  
            strftime('%I:%M %p', sunrise) AS Sunrise,   
            strftime('%I:%M %p', sunset) AS Sunset
        FROM chart
    """

    # Parametrized filtering
    if selected_city:
        query = f"{base_query} WHERE location = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, db, params=(selected_city,))
    elif current_location:
        query = f"{base_query} WHERE location = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, db, params=(current_location,))
    else:
        query = f"{base_query} ORDER BY created_at DESC"
        df = pd.read_sql_query(query, db)

    # Distinct city dropdown query
    cities_df = pd.read_sql_query("SELECT DISTINCT location FROM chart WHERE location IS NOT NULL ORDER BY location", db)

    # Format datetime columns 
    if 'Time' in df.columns and not df['Time'].empty:
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

    # Convert DataFrame to Bootstrap-styled HTML table
    weather_table_html = df.fillna('').to_html(
        classes='table table-striped table-bordered table-hover',
        index=False,
        escape=True
    )

    cities_list = cities_df['location'].tolist()
    return render_template(
        'weather.html',
        table=weather_table_html, 
        cities=cities_list, 
        selected_city=selected_city
    )

@bp.route('/api/latest-temp')
def latest_temp():
    location = os.environ.get("CURRENT_LOCATION")
    db = get_db()
    
    row = db.execute(
        "SELECT temperature FROM chart WHERE location = ? ORDER BY created_at DESC LIMIT 1",
        (location,)
    ).fetchone()
    
    temp = f"{row['temperature']}°" if row and row['temperature'] is not None else "N/A"
    return jsonify({"temperature": temp})

@bp.route('/api/latest-humidity')
def latest_humidity():
    location = os.environ.get("CURRENT_LOCATION")
    db = get_db()
    
    row = db.execute(
        "SELECT humidity FROM chart WHERE location = ? ORDER BY created_at DESC LIMIT 1",
        (location,)
    ).fetchone()
    
    humidity = f"{row['humidity']}" if row and row['humidity'] is not None else "N/A"
    return jsonify({"humidity": humidity})

@bp.route('/api/latest-windspeed')
def latest_windspeed():
    location = os.environ.get("CURRENT_LOCATION")
    db = get_db()
    
    row = db.execute(
        "SELECT windspeed FROM chart WHERE location = ? ORDER BY created_at DESC LIMIT 1",
        (location,)
    ).fetchone()
    
    windspeed = f"{row['windspeed']}" if row and row['windspeed'] is not None else "N/A"
    return jsonify({"windspeed": windspeed})

@bp.route('/api/latest-wind-direction')
def latest_wind_direction():
    location = os.environ.get("CURRENT_LOCATION", "DefaultCity")
    db = get_db()
    
    # Adjust column name to match your database schema (e.g., wind_direction or wind_degrees)
    row = db.execute(
        "SELECT winddirection FROM chart WHERE location = ? ORDER BY created_at DESC LIMIT 1",
        (location,)
    ).fetchone()
    
    degrees = row['winddirection'] if row and row['winddirection'] is not None else None
    return jsonify({"wind_degrees": degrees})

@bp.route('/api/current-location')
def current_location():
    location = os.environ.get("CURRENT_LOCATION", "Unknown Location")
    return jsonify({"location": location})

index = weather

if __name__ == "__main__":
    from flaskr import create_app
    app = create_app()
    post_weather_updates_from_db(app, author_id=1)
