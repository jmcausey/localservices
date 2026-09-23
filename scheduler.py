#!/usr/bin/env python3

import os
import sys
import time
import argparse
from pathlib import Path
from schedule import repeat, every, run_pending
from datetime import datetime
from typing import Any

# Add ~/local/flaskr to Python path
flaskr_dir = Path(__file__).resolve().parent / "flaskr"
if str(flaskr_dir) not in sys.path:
    sys.path.append(str(flaskr_dir))

# Import application factory and task functions
from flaskr import create_app, get_db
from scrapers.kevinmd import run_scraper as kevinmd_scraper
from scrapers.informaticsinc import run_scraper as informaticsinc
from scrapers.cl_surfboards import run_scraper as clsurfboards
from scrapers.cl_freestuff import run_scraper as clfreestuff
from weather_tasks import (
    fetch_weather, 
    post_weather_updates_from_db, 
    graph1
)
from astronomy_tasks import (
    post_apod_to_blog, 
    post_astronomy_data_to_blog
)

LOCATIONS_FILE = os.path.expanduser('~/local/data/locations/locations.json')
CURRENT_LOCATION = os.environ.get("CURRENT_LOCATION")

# Instantiate Flask app once for context access
app = create_app()

@repeat(every().hour)
def weather_update():
    fetch_weather()
    
@repeat(every().day.at("08:00"))
@repeat(every().day.at("20:00"))
def daily_update():
    # Handles fetching data, DB insert, dial image generation, and single blog post
    post_astronomy_data_to_blog(app, author_id=1)
    informaticsinc()
    clfreestuff()
    clsurfboards()
    post_apod_to_blog(app, author_id=1)    

@repeat(every().minute)
def cleanup_completed_posts():
    """Removes posts marked as 'complete' from the database."""
    with app.app_context():
        db = get_db()
        cursor = db.execute("DELETE FROM post WHERE status = 'complete'")
        db.commit()
        count = cursor.rowcount
        print(f"[{datetime.now()}] Cleanup ran: removed {count} completed post(s).")


# Registry of individual executable startup jobs indexed for targeted startup execution
STARTUP_JOBS = [
    ("cleanup_completed_posts", lambda: cleanup_completed_posts()),
    ("weather_update", lambda: weather_update()),
    ("post_apod_to_blog", lambda: post_apod_to_blog(app, author_id=1)),
    ("post_astronomy_data_to_blog", lambda: post_astronomy_data_to_blog(app, author_id=1)),
    ("post_weather_updates_from_db", lambda: post_weather_updates_from_db(app, author_id=1)),
    ("informaticsinc", lambda: informaticsinc()),
    ("kevinmd_scraper", lambda: kevinmd_scraper()),
    ("clsurfboards", lambda: clsurfboards()),
    ("clfreestuff", lambda: clfreestuff()),
]


def execute_startup_jobs(option: Any = False):
    """
    Executes startup jobs based on provided option parameter:
      - False / None / "False": Runs no startup jobs.
      - True / "all" / "True-All": Executes all registered startup jobs.
      - int / list / tuple / str: Executes jobs matched by index or name.
    """
    if not option or option is False or str(option).lower() in ("false", "none", "0"):
        print("[Startup] No startup jobs requested.")
        return

    # Standardize string representations of 'True-All' or 'all'
    if option is True or str(option).strip().lower() in ("true", "true-all", "all"):
        target_indices = list(range(len(STARTUP_JOBS)))
    elif isinstance(option, int):
        target_indices = [option]
    elif isinstance(option, (list, tuple)):
        target_indices = option
    elif isinstance(option, str):
        # Parses comma-separated string choices like "0,2,4" or single integer strings "3"
        parts = [p.strip() for p in option.split(",")]
        target_indices = []
        for p in parts:
            if p.isdigit():
                target_indices.append(int(p))
            else:
                target_indices.append(p)
    else:
        target_indices = [option]

    print(f"[{datetime.now()}] Running initial startup jobs...")

    for target in target_indices:
        job_name, job_func = None, None

        if isinstance(target, int):
            if 0 <= target < len(STARTUP_JOBS):
                job_name, job_func = STARTUP_JOBS[target]
            else:
                print(f"  [!] Skipping invalid job index: {target}")
                continue
        elif isinstance(target, str):
            # Match by job name string if provided
            matched = [j for j in STARTUP_JOBS if j[0].lower() == target.lower()]
            if matched:
                job_name, job_func = matched[0]
            else:
                print(f"  [!] Skipping unrecognized job name: '{target}'")
                continue

        if job_func:
            try:
                print(f"  [>] Executing startup job: {job_name}")
                job_func()
            except Exception as e:
                print(f"  [!] Error executing startup job '{job_name}': {e}")


def parse_arguments():
    """Parses command-line options and generates custom help descriptions."""
    # Build dynamic job list for the help manual display
    job_catalog = "\n".join(
        f"    [{index}] {name}" for index, (name, _) in enumerate(STARTUP_JOBS)
    )

    description = "Task Scheduler Daemon with optional startup job execution."
    epilog = f"""
Startup Job Options (POSITIONAL or --startup):
  False                  Skip all startup tasks (Default).
  True / True-All / all  Run every registered startup task.
  <index>                Run a specific job by numeric index (e.g., '2').
  <index1,index2,...>    Run multiple specific jobs (e.g., '0,3,5').
  <job_name>             Run job by string name (e.g., 'weather_update').

Registered Startup Jobs:
{job_catalog}

Examples:
  python scheduler.py --help
  python scheduler.py False
  python scheduler.py True-All
  python scheduler.py 3
  python scheduler.py 0,2,4
  python scheduler.py --startup weather_update
"""

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "startup_pos",
        nargs="?",
        default=None,
        help="Optional positional argument specifying startup jobs (e.g., 'False', 'True-All', '0,2')."
    )

    parser.add_argument(
        "-s", "--startup",
        dest="startup_opt",
        default=None,
        help="Explicit flag for startup option (e.g., --startup True-All or --startup 3)."
    )

    args = parser.parse_args()

    # Prioritize explicit --startup option over positional argument, defaulting to False
    startup_value = args.startup_opt or args.startup_pos or False
    return startup_value


if __name__ == "__main__":
    startup_arg = parse_arguments()

    try:
        execute_startup_jobs(startup_arg)
    except Exception as e:
        print(f"Error during initial startup run: {e}")

    print('Starting scheduler loop...')
    daily_update()
    while True:
        run_pending()
        time.sleep(1)