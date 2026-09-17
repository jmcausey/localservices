# LocalServices Platform

*An automated Flask-based web application and intelligence platform designed for multi-source web scraping, background task orchestration, and specialized kiosk presentations.*

## Core Features

* **Automated Scrapers (`flaskr/scraper/`):** Targeted extraction modules for East Texas Free Stuff (`cat=zip`), Athens-area Craigslist surfboards (100-mile radius), Informatics Inc., and KevinMD Tech. Enforces strict filtering by excluding "modem" keywords and pruning posts older than 24 hours.
* **Background Task Automation (`scheduler.py`):** Multi-run execution orchestrator triggering ingestion pipelines and astronomy data publishing twice daily at 08:00 and 20:00.
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
| `flaskr/scraper/` | Modular web scraping scripts for Craigslist, Informatics, and KevinMD |
| `flaskr/templates/` | Jinja2 templates (standard, scrolling teleprompter, and audio kiosk layouts) |
| `scheduler.py` | Background execution script for scheduled task windows |

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/jmcausey/localservices.git](https://github.com/jmcausey/localservices.git)
   cd localservices

## Credits

   Platform architecture and automation logic co-developed by Gemini, built on open-source foundations provided by the Python Software Foundation, Pallets (Flask), SQLite, BeautifulSoup, and gTTS.