LocalServices Dashboard & Automation Platform
A modular Flask-based web application and automated intelligence platform designed for multi-source web scraping, background task orchestration, and specialized kiosk presentation formats.

Architecture & Tech Stack
Backend Framework: Flask (Application Factory pattern with Blueprints)

Database: SQLite with BLOB-to-string decoding and dynamic status tracking (new, pending, complete)

Task Automation: Python schedule runner executing jobs twice daily

Audio & Media: Google Text-to-Speech (gTTS) backend streaming with dynamic image embedding and OpenGraph extraction

Core Features
Automated Scrapers (flaskr/scraper/): Targeted extraction modules for regional content, including East Texas Free Stuff (cat=zip), Athens-area Craigslist surfboards (100-mile radius), Informatics Inc., and KevinMD Tech. Includes strict keyword filtering (excluding "modem") and 24-hour timestamp pruning.

Background Task Scheduler (scheduler.py): Automated orchestration triggering ingestion pipelines and astronomy data publishing twice daily at 08:00 and 20:00.

Live Polling Dashboard (/): Real-time feed monitoring that polls /api/latest-post-id every 10 seconds to auto-refresh upon new database insertions.

Teleprompter Feed (/scrolling): Locked-viewport continuous vertical scrolling container with hover-to-pause reading controls.

Audio Kiosk Reader (/kiosk): Single-post presentation view utilizing on-the-fly gTTS audio streaming via /audio/<id>, a 10-second post-playback pause, and automated carousel rotation.

Project Structure
Directory / File	Description
flaskr/	Core application logic, database models, and authentication blueprint
flaskr/blog.py	Blueprint routing for post management, API endpoints, and audio streaming
flaskr/scraper/	Modular web scraping scripts for Craigslist, Informatics, and KevinMD
flaskr/templates/	Jinja2 templates including standard, scrolling, and kiosk UI layouts
scheduler.py	Background runner for scheduled multi-run execution windows
Getting Started
Clone the repository:

Bash
git clone https://github.com/jmcausey/localservices.git
cd localservices
Install dependencies:

Bash
pip install -r requirements.txt
Initialize the database:

Bash
flask --app flaskr init-db
Run the Flask application:

Bash
flask --app flaskr run
Start background automation:

Bash
python scheduler.py