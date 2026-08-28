#!/usr/bin/env python

import time
import requests
import sqlite3

api_key = "5c4b09fdb3cbf0962a16af90febbf116" 
#Malakoff, TX USA
lat = "32.225"
lon = "-96.008"

def get_weather_by_coords(lat, lon, api_key, units="metric"):
    # Base URL for the OpenWeatherMap Current Weather Data API
    base_url = "https://api.openweathermap.org/data/2.5/weather"

    # Define query parameters
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units  # 'metric' for Celsius, 'imperial' for Fahrenheit, 'standard' for Kelvin
    }

    try:
        # Send the GET request
        response = requests.get(base_url, params=params)

        # Raise an exception for bad status codes (e.g., 401 Unauthorized, 404 Not Found)
        response.raise_for_status()

        # Parse response payload to a dictionary
        weather_data = response.json()
        return weather_data

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

data = get_weather_by_coords(lat, lon, api_key, units="imperial")

if data:
        # Safely extract specific weather fields from the JSON payload
        location = data["name"]
        geolocation = "32.225,-96.008" #data["coords"]
        description = data["weather"][0]["description"]
        tempurature = data["main"]["temp"]
        pressure = data["main"]["pressure"]
        feelslike = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        visibility = data["visibility"]
        windspeed = data["wind"]["speed"]
        winddirection = data["wind"]["deg"]
        clouds = str(data["clouds"])
        sunrise = data["sys"]["sunrise"]
        sunset = data["sys"]["sunset"]

        #print(f" Weather for {location_name} ({latitude}, {longtitude}):")


with sqlite3.connect('/home/jon/local/weatherwise/data/weatherdb.sqlite') as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                location TEXT,
                geolocation TEXT,
                description TEXT,
                tempurature TEXT,
                pressure TEXT,
                feelslike TEXT,
                humidity TEXT,
                visibility TEXT,
                windspeed TEXT,
                winddirection TEXT,
                clouds TEXT,
                sunrise TEXT,
                sunset TEXT
                )
         ''')

        cursor.execute('''
            INSERT INTO chart (
                location, geolocation, description, tempurature, pressure, 
                feelslike, humidity, visibility, windspeed, winddirection, 
                clouds, sunrise, sunset) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', 
                (location, geolocation, description, tempurature, pressure, 
                feelslike, humidity, visibility, windspeed, winddirection, 
                clouds, sunrise, sunset))

        time.sleep(0.5)

cursor.close()
conn.close()
