#!/usr/bin/env python

import time
import requests
import sqlite3

api_key = "5c4b09fdb3cbf0962a16af90febbf116" 

#Key U.S. State Capital Coordinates
locations = {"Albany, New York" : "42.650,-73.750",
    "Annapolis, Maryland" : "38.970,-76.490",
    "Austin, Texas" : "30.270,-97.740",
    "Bismarck, North Dakota" : "46.810,-100.780",
    "Boise, Idaho" : "43.610,-116.200",
    "Boston, Massachusetts" : "42.36,-71.050",
    "Carson City, Nevada" : "39.160,-119.760",
    "Charleston, West Virginia" : "38.340,-81.630",
    "Cheyenne, Wyoming" : "41.140,-104.820",
    "Columbia, South Carolina" : "34.000,-81.030",
    "Columbus, Ohio" : "39.960,-82.990",
    "Concord, New Hampshire" : "43.200,-71.530",
    "Denver, Colorado" : "39.730,-104.980",
    "Des Moines, Iowa" : "41.580,-93.600",
    "Dover, Delaware" : "39.160,-75.520",
    "Frankfort, Kentucky" : "38.190,-84.870",
    "Harrisburg, Pennsylvania" : "40.270,-76.880",
    "Hartford, Connecticut" : "41.760,-72.670",
    "Helena, Montana" : "46.590,-112.020",
    "Honolulu, Hawaii" : "21.300,-157.820",
    "Indianapolis, Indiana" : "39.760,-86.150",
    "Jackson, Mississippi" : "32.290,-90.180",
    "Jefferson City, Missouri" : "38.570,-92.170",
    "Juneau, Alaska" : "58.300,-134.410",
    "Lansing, Michigan" : "42.730,-84.550",
    "Lincoln, Nebraska" : "40.810,-96.680",
    "Little Rock, Arkansas" : "34.730,-92.330",
    "Madison, Wisconsin" : "43.070,-89.400",
    "Montgomery, Alabama": "32.360,-86.270",
    "Montpelier, Vermont" : "44.260,-72.570",
    "Nashville, Tennessee" : "36.160,-86.780",
    "Oklahoma City, Oklahoma" : "35.460,-97.510",
    "Olympia, Washington": "47.040,-122.890",
    "Phoenix, Arizona" : "33.440,-112.070",
    "Pierre, South Dakota" : "44.360,-100.350",
    "Providence, Rhode Island" : "41.820,-71.410",
    "Raleigh, North Carolina" : "35.770,-78.630",
    "Richmond, Virginia" : "37.540,-77.440",
    "Sacramento, California" : "38.550,-121.460",
    "Salem, Oregon" : "44.940,-123.030",
    "Salt Lake City, Utah" : "40.760,-111.890",
    "Santa Fe, New Mexico" : "35.680,-105.930",
    "Springfield, Illinois" : "39.780,-89.650",
    "St. Paul, Minnesota" : "44.950,-93.090",
    "Tallahassee, Florida" : "30.430,-84.280",
    "Topeka, Kansas" : "39.050,-95.680",
    "Trenton, New Jersey" : "40.220,-74.750",
    "Baton Rouge, Louisiana" : "30.450,-91.140",
    "Atlanta, Georgia" : "33.740,-84.380",
    "Washington, D.C. (Federal District)" : "38.890,-77.030",
    "San Juan, Puerto Rico (Territory)" : "18.460,-66.110" }

#for k,v in geolist.items():
#    print('update-weather ' + k)
#    subprocess.call(['/home/jon/bin/update-weather',str(v)])
#    time.sleep(0.2)


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

for k,v in locations.items():
    city = k
    geo = v.split(",")
    latitude = geo[0]
    longtitude = geo[1]
    data = get_weather_by_coords(latitude, longtitude, api_key, units="imperial")

    if data:
        # Safely extract specific weather fields from the JSON payload
        location = data["name"]
        geolocation = k #data["coords"]
        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
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
        

# 1. Added quotes around the file path
    with sqlite3.connect('/home/jon/local/weatherwise/data/weather.sqlite') as conn:
        cursor = conn.cursor()
    
    # 2. Created table string with proper closing quotes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                location TEXT,
                geolocation TEXT,
                description TEXT,
                temperature TEXT,
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
                location, geolocation, description, temperature, pressure, 
                feelslike, humidity, visibility, windspeed, winddirection, 
                clouds, sunrise, sunset) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', 
                (location, geolocation, description, temperature, pressure, 
                feelslike, humidity, visibility, windspeed, winddirection, 
                clouds, sunrise, sunset))

        time.sleep(0.5)

cursor.close()
conn.close()
