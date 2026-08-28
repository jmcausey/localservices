import os
import pandas as pd
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv
import socket
from flask import Blueprint, render_template, request
from flaskr.db import get_db

bp = Blueprint('weather', __name__)
hostname = socket.gethostname()

LOCATIONS_FILE = "/home/jon/local/weatherwise/data/locations.json"

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
        app.logger.error(f"Failed to load locations file: {e}")
        return {}

def get_location_coordinates(location_query: str) -> Tuple[Optional[float], Optional[float]]:
    """Looks up geolocation metrics for a specific city query string."""
    locations_map = load_locations()
    for name, coords in locations_map.items():
        if location_query.lower() in name.lower():
            return coords[0], coords[1]
    return None, None

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

index = weather
