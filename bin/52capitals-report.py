#!/usr/bin/env python

import time
import subprocess
import sqlite3
import pprint
import math

with sqlite3.connect("/home/jon/local/weatherwise/data/weatherdb.sqlite") as conn:
    # 2. Create a cursor object to execute commands
    cursor = conn.cursor()

    # 3. Execute the SQL read query
    locations = cursor.execute("SELECT location FROM chart").fetchall()
    #locations = [' '.join(tup) for tup in  location]
    for l in locations:
         id = cursor.execute("SELECT id FROM chart WHERE location LIKE ? ORDER BY id DESC LIMIT 1" , (l),).fetchone()
         location = l[0] 
         created_at = cursor.execute("SELECT created_at FROM chart WHERE id = ? ORDER BY created_at DESC LIMIT 1 ", (id),).fetchone()
         tempurature = cursor.execute("SELECT tempurature FROM chart WHERE id = ?" , (id),).fetchone()
         wind_speed = cursor.execute("SELECT windspeed FROM chart WHERE id = ?" , (id),).fetchone()
         wind_direction = cursor.execute("SELECT winddirection FROM chart WHERE id = ?" , (id),).fetchone()
         print('The weather in ', str(location) ,'is ', math.ceil(float(tempurature[0])), 'Fahrenheit', 'and the windspeed is ' , math.ceil(float(wind_speed[0])), 'miles per hour',  'moving at ' ,wind_direction[0] ,'degrees')

