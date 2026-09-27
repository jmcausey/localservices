# LocalServices Platform

*An automated Flask-based web application and intelligence platform designed for multi-source web scraping, background task orchestration, and specialized kiosk presentations.*

## Core Features

* **Craigslist scheduler:** The CL > Search Jobs page manages daily Craigslist jobs, including the seeded East Texas pets (06:00), surfboards (08:00, 20:00), and free-stuff (08:00, 20:00) schedules. Jobs can be added, edited, and disabled. Unique Craigslist IDs prevent repeated imports.
* **Craigslist feed (`/cl`):** Shows all linked and legacy Craigslist posts separately from the general `/` blog feed. `/cl-pets` filters the feed to pet-category listings; both routes use the same visibility and status rules.
* **Control panel (`/control-panel`):** Filters and manages stored blog posts. Scheduled Craigslist jobs are managed separately under CL > Search Jobs.
* **System logs (`/control-panel/system-logs`):** Displays recent Flask application logs stored in SQLite. The page requires login and supports severity filtering.
* **Live feed (`/`):** Polls `/api/latest-post-id` every 10 seconds and refreshes when a newer post is available.
* **Scrolling feed (`/scrolling`):** Displays posts in a continuous scrolling view with hover-to-pause behavior.
* **Audio kiosk (`/kiosk`):** Reads posts aloud using `gTTS` through `/audio/<id>`.

## Tech Stack & Architecture

| Component | Technology |
| :--- | :--- |
| **Backend** | Flask (Application Factory pattern with Blueprints) |
| **Database** | SQLite for Craigslist listings, blog posts, weather, astronomy, network events, and application logs; blog posts use `new`, `pending`, and `complete` statuses |
| **Automation** | Python `schedule` runner |
| **Media / Audio** | Google Text-to-Speech (`gTTS`) streaming, OpenGraph metadata extraction |

## Project Structure

| Path | Purpose |
| :--- | :--- |
| `flaskr/` | Core application factory, database models, and authentication blueprint |
| `flaskr/blog.py` | Blueprint routing for post lifecycle management, API endpoints, and audio streaming |
| `flaskr/scrapers/` | Craigslist and other web scraping modules |
| `flaskr/system_logging.py` | SQLite logging handler installed by the Flask application factory |
| `flaskr/templates/` | Jinja2 templates (standard, scrolling teleprompter, and audio kiosk layouts) |
| `scheduler.py` | Background execution script for scheduled task windows |

## Getting Started

1. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   flask --app flaskr init-db
   ```

3. **Run the Flask application:**
   ```bash
   flask --app flaskr run
   ```

4. **Start the scheduler** in another terminal:
   ```bash
   python scheduler.py
   ```

5. **Run the tests:** Install `pytest` if needed, then run:
   ```bash
   python -m pip install pytest
   python -m pytest flaskr/tests -q
   ```

6. **Preview the documentation site:**
   ```bash
   mkdocs serve
   ```

   MkDocs reads its pages from `flaskr/docs/`.

## Credits

   Platform architecture and automation logic co-developed by Gemini, built on open-source foundations provided by the Python Software Foundation, Pallets (Flask), SQLite, BeautifulSoup, and gTTS.