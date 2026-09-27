# LocalServices

LocalServices is a Flask application for collecting and presenting scraped listings, weather and astronomy data, network events, and application diagnostics. It uses SQLite for persistent data and Flask blueprints for its application areas.

## Blog Feed

The root route (`/`) displays general blog posts. A daily job at 06:00 local time checks the East Texas community/pets category and imports every new, unique listing returned within the scraper's 24-hour freshness window. Scraped Craigslist data is stored separately in `craigslist_postings`, keyed by Craigslist's unique listing ID, and linked to a blog post. Pet-category blog posts appear at `/cl-pets` and are excluded from `/`. The structured record can include the raw and numeric price, location and coordinates, listing URL, category, search query, posting and scrape timestamps, image URL, and description. Both feeds show blog posts created within the last 24 hours, keep `pending` posts visible indefinitely, and hide `complete` posts immediately. Hiding a post does not delete either record. The `/scrolling` and `/kiosk` views currently display all blog posts without applying these feed filters.

The root feed checks `/api/latest-post-id` every 10 seconds and reloads when a newer post is available. The audio endpoint `/audio/<id>` generates speech from a post using gTTS.

## Control Panel and Logs

Authenticated users can submit Craigslist searches and filter stored posts at `/control-panel`. The **System Logs** page at `/control-panel/system-logs` displays up to 250 recent Flask application log entries and can filter by severity. The logging handler stores `INFO` and higher records, including source location and exception details, in the `system_logs` SQLite table.

## Development

Run the test suite from the repository root:

```bash
python -m pytest flaskr/tests -q
```

Install `pytest` separately if it is not available in the active Python environment. Run `mkdocs serve` from the repository root to preview this documentation site.

## Module Reference

* [Application factory](__init__.py.md)
* [Blog and API routes](blog.py.md)
* [Control panel](control.py.md)
* [Database schema](schema.sql.md)
* [Weather](weather.py.md)
* [Astronomy](astronomy.py.md)
* [Network](network.py.md)