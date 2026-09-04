#!/usr/bin/env python3

import os
import sys
import time
import subprocess
from pathlib import Path
import schedule
import sys
from pathlib import Path

# Add ~/local/flaskr to Python path
flaskr_dir = Path(__file__).resolve().parent / "flaskr"
sys.path.append(str(flaskr_dir))

# Import directly from weather_tasks
from weather_tasks import fetch_weather, post_weather_updates_from_db, graph1

# Explicitly register project paths
BASE_DIR = Path(__file__).resolve().parent
SERVICE_DIR = BASE_DIR / "services"

for path in [str(BASE_DIR), str(SERVICE_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Debug check before importing
openweather_path = SERVICE_DIR / "weather" / "openweather.py"
if not openweather_path.exists():
    print(f"ERROR: Expected file at '{openweather_path}' but it was not found!")
    print(f"Current Working Directory: {os.getcwd()}")
    sys.exit(1)

from weather.openweather import fetch_weather

#def run_network_scan_job():
#    """Triggers the root-privileged scapy network scanner via subprocess."""
#    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] * Starting automated network scan...")
#    
#    command = [
#        "sudo", "-H", 
#        "/home/jon/.pyenv/versions/3.13.7/bin/python", 
#        "-m", "flaskr.scanner"
#    ]
#    
#    try:
#        # Run command from BASE_DIR so python module pathing matches perfectly
#        result = subprocess.run(
#            command, 
#            cwd=str(BASE_DIR),
#            capture_output=True, 
#            text=True, 
#            check=True
#        )
#        print("[+] Scanner Output:")
#        print(result.stdout.strip())
#        
#    except subprocess.CalledProcessError as e:
#        print(f"[-] Network scanner failed with exit code {e.returncode}", file=sys.stderr)
#        print(f"[-] Error details:\n{e.stderr.strip()}", file=sys.stderr)

def hourly_weather():
    subprocess.run(["python3","-m","flaskr.weather"])

def hourly_astronomy():
    subprocess.run(["python3","-m","flaskr.astronomy"])

def daily_astronomy():
    subprocess.run(["python3","/home/jon/local/services/astronomy/ipgeolocation.py"])

# Schedule Jobs
# 1. Weather job runs every 15 minutes
schedule.every(15).minutes.do(fetch_weather)

# 2. Network scan job runs every 15 minutes (or adjust as needed)
#schedule.every(15).minutes.do(run_network_scan_job)

schedule.every().hour.at(":00").do(hourly_weather)
schedule.every().day.at("08:00").do(hourly_astronomy)
schedule.every().day.at("00:00").do(daily_astronomy)

print("Scheduler started. Press Ctrl+C to stop.")

# Run both jobs immediately once on startup
fetch_weather()
hourly_weather()
daily_astronomy()
hourly_astronomy()
#run_network_scan_job()

# Main orchestration loop
while True:
    schedule.run_pending()
    time.sleep(1)
