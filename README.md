# LocalServices Platform

*An automated Flask-based web application and intelligence platform designed for multi-source web scraping, background task orchestration, and specialized kiosk presentations.*

## Core Features

* **Automated Scrapers (`flaskr/scraper/`):** Targeted extraction modules for online posts and pruning posts older than 24 hours.
* **Background Task Automation (`scheduler.py`):** Multi-run execution orchestrator triggering ingestion pipelines.
* **Live Polling Dashboard (`/`):** Real-time feed monitoring that polls `/api/latest-post-id` every 10 seconds to auto-refresh upon new database insertions.
* **Teleprompter Feed (`/scrolling`):** Locked-viewport continuous vertical scrolling container with interactive hover-to-pause controls.
* **Audio Kiosk Reader (`/kiosk`):** Single-post presentation view utilizing on-the-fly `gTTS` audio streaming via `/audio/<id>`, a 10-second post-playback pause, and automated carousel rotation.

## Tech Stack & Architecture

| Component | Technology |
| :--- | :--- |
| **Backend** | Flask (Application Factory pattern with Blueprints) |
| **Database** | SQLite with BLOB-to-string decoding & dynamic status management (`new`, `pending`, `complete`) |
| **Automation** | Python `schedule` runner |
| **Media / Audio** | Google Text-to-Speech (`gTTS`) streaming, OpenGraph metadata extraction |

## Project Structure

| Path | Purpose |
| :--- | :--- |
| `flaskr/` | Core application factory, database models, and authentication blueprint |
| `flaskr/blog.py` | Blueprint routing for post lifecycle management, API endpoints, and audio streaming |
| `flaskr/scraper/` | Modular web scraping scripts  |
| `flaskr/templates/` | Jinja2 templates (standard, scrolling teleprompter, and audio kiosk layouts) |
| `scheduler.py` | Background execution script for scheduled task windows |

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/jmcausey/localservices.git](https://github.com/jmcausey/localservices.git)
   cd localservices

2. **Install dependancies:**
   ```bash 
   pip install -r requirements.txt

3. **Initialize the database:**
   ```bash 
   flask --app flaskr init-db

4. **Run the flask application:**
   ```bash 
   flask --app flaskr run

5. **Start background task automation:**
   ```bash
   python scheduler.py

## Credits

   Platform architecture and automation logic co-developed by Gemini, built on open-source foundations provided by the Python Software Foundation, Pallets (Flask), SQLite, BeautifulSoup, and gTTS.