# LocalServices

LocalServices is a Flask application for collecting and presenting scraped listings, weather and astronomy data, network events, and application diagnostics. It uses SQLite for persistent data and Flask blueprints for its application areas.

## Blog Feed

The root route (`/`) displays blog posts. Craigslist listings are stored in the `post` table as `new` posts. The root feed shows posts created within the last 24 hours, keeps `pending` posts visible indefinitely, and hides `complete` posts immediately. Hiding a post does not delete it. The `/scrolling` and `/kiosk` views currently display all posts without applying the root feed's age and status filters.

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