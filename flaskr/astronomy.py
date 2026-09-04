import sqlite3
import os
import pandas as pd
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime
import socket
from flask import Blueprint, render_template, request
from flaskr.db import get_db
from flaskr.blog import create_post


DATABASE = os.path.expanduser('~/local/data/flaskr.sqlite')

bp = Blueprint('astronomy', __name__)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name: row['city']
    return conn

def post_astro_updates_from_db(app, author_id=1):
    """
    Reads weather logs from the DB and creates a new weather blog post.
    Must run within Flask app context.
    """
    with app.app_context():
        db = get_db()
        
        # 1. Fetch astrological data from your database
        astro_rows = db.execute("""
            SELECT location, state_prov, country_name, sunrise, sunset, solar_noon, day_length, 
            sun_altitude, sun_distance, sun_azimuth, moon_phase, moonrise, moonset, 
            moon_altitude, moon_distance, moon_azimuth, moon_parallactic_angle, moon_illumination_percentage, moon_angle
            FROM astronomy
            ORDER BY timestamp DESC LIMIT 1
        """).fetchall()

        if not astro_rows:
            print("No weather data found in DB.")
            return

        location = astro_rows[0]['location']
        state = astro_rows[0]['state_prov']
        country = astro_rows[0]['country_name']
        sunrise = astro_rows[0]['sunrise']
        sunset = astro_rows[0]['sunset']
        solar_noon = astro_rows[0]['solar_noon']
        day_length = astro_rows[0]['day_length']
        sun_altitude = astro_rows[0]['sun_altitude']
        sun_distance = astro_rows[0]['sun_distance']
        sun_azimuth = astro_rows[0]['sun_azimuth']
        moon_phase = astro_rows[0]['moon_phase']
        moon_rise = astro_rows[0]['moonrise']
        moon_set = astro_rows[0]['moonset']
        moon_altitude = astro_rows[0]['moon_altitude']
        moon_parallactic_angle = astro_rows[0]['moon_parallactic_angle']
        moon_illumination_percentage = astro_rows[0]['moon_illumination_percentage']
        moon_angle = astro_rows[0]['moon_angle']

        # 2. Format rows into your styled HTML .table markup
        table_rows = "".join(
            f"\n"
            f"sunrise: {sunrise} | "
            f"sunset: {sunset} | "
            f"solar noon: {solar_noon} | "
            f"day length: {day_length} | "
            f"sun altitude: {sun_altitude} | "
            f"sun distance: {sun_distance} | "
            f"sun azimuth: {sun_azimuth} | "
            f"moon phase: {moon_phase} | "
            f"moon rise: {moon_rise} | "
            f"moon set: {moon_set} | "
            f"moon altitude: {moon_altitude} | "
            f"moon parallactic angle: {moon_parallactic_angle} | "
            f"moon illumination percentage: {moon_illumination_percentage} | "
            f"moon angle {moon_angle} "
            for row in astro_rows
        )

        # 3. Access blog creation API logic directly
        title = f"{location} {state} {country} astronomy - {datetime.now().strftime('%I:%M %p')}"
        body = f"{table_rows}"
        #add celestial_dial function that creates image and returns filename
        image_file = ''
        
        create_post(title=title, body=body, image_file=image_file, author_id=author_id)
        print(f"Successfully posted: '{title}'")


@bp.route('/')
@bp.route('/astronomy')
def astronomy_table():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM astronomy ORDER BY timestamp DESC').fetchall()
    conn.close()
    
    return render_template('astronomy.html', records=records)

if __name__ == "__main__":
    from flaskr import create_app
    app = create_app()
    post_astro_updates_from_db(app, author_id=1)
