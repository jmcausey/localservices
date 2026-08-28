#!/usr/bin/env python

import time
import subprocess
import sqlite3
import pprint
import math

def Wdirection(deg):
    if 0 <= wind_direction <= 12 or 348 <= wind_direction <= 360:
        wd = 'North'
    elif 11 <= wind_direction <= 35:
        wd = 'North Northeast'
    elif 33 <= wind_direction <= 56:
        wd = 'Northeast'
    elif 56 <= wind_direction <= 79:
        wd = 'East Northeast'
    elif 78 <= wind_direction <= 101:
        wd = 'East'
    elif 101 <= wind_direction <= 123:
        wd = 'East Southeast'
    elif 123 <= wind_direction <= 146:
        wd = 'Southeast'
    elif 146 <= wind_direction <= 168:
        wd = 'East Southeast'
    elif 168 <= wind_direction <= 191:
        wd = 'South'
    elif 191 <= wind_direction <= 213:
        wd = 'South Southwest'
    elif 213 <= wind_direction <= 236:
        wd = 'Southwest'
    elif 236 <= wind_direction <= 258:
        wd = 'West Southwest'
    elif 258 <= wind_direction <= 281:
        wd = 'West'
    elif 281 <= wind_direction <= 303:
        wd = 'West Northwest'
    elif 303 <= wind_direction <= 326:
        wd = 'Northwest'
    else:
        wd = 'Unknown'
    return wd

with sqlite3.connect("/home/jon/local/weatherwise/data/weatherdb.sqlite") as conn:
    cursor = conn.cursor()
    location = "Malakoff, TX"
    id = cursor.execute("SELECT id FROM chart WHERE location LIKE '%Malakoff%' ORDER BY id DESC LIMIT 1").fetchone()
    created_at = cursor.execute("SELECT created_at FROM chart WHERE id = ? ORDER BY created_at DESC LIMIT 1 ", (id),).fetchone()
    tempurature = cursor.execute("SELECT tempurature FROM chart WHERE id = ?" , (id),).fetchone()
    wind_speed = cursor.execute("SELECT windspeed FROM chart WHERE id = ?" , (id),).fetchone()
    wind_direction = math.ceil(int(cursor.execute("SELECT winddirection FROM chart WHERE id = ?" , (id),).fetchone()[0]))
    print('The weather in', str(location) ,'is')
    print(f"{math.ceil(float(tempurature[0]))}\N{DEGREE SIGN} Fahrenheit, and the windspeed is")
    print(math.ceil(float(wind_speed[0])), 'miles per hour',  'moving' ,Wdirection(wind_direction))

