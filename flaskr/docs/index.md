# LocalServices

LocalServices is a Flask application for collecting and presenting scraped listings, weather and astronomy data, network events, and application diagnostics. It uses SQLite for persistent data and Flask blueprints for its application areas.

## Blog Feed

The root route (`/`) displays general blog posts. Craigslist job definitions are managed at `/control-panel/cl-jobs` under the CL subnav. The scheduler polls saved jobs each minute and runs enabled jobs at their configured local daily times. Defaults are pets at 06:00 and surfboards/free stuff at 08:00 and 20:00. New listings are stored in `craigslist_postings`, keyed by Craigslist's unique listing ID, and linked to a blog post. Craigslist posts appear at `/cl` and are excluded from `/`; `/cl-pets` filters that feed to pet listings. Both feeds show blog posts created within the last 24 hours, keep `pending` posts visible indefinitely, and hide `complete` posts immediately. Hiding a post does not delete either record. The `/scrolling` and `/kiosk` views currently display all blog posts without applying these feed filters.

The root feed checks `/api/latest-post-id` every 10 seconds and reloads when a newer post is available. The audio endpoint `/audio/<id>` generates speech from a post using gTTS.

## Control Panel and Logs

Authenticated users can filter stored posts at `/control-panel` and add or modify scheduled Craigslist jobs at `/control-panel/cl-jobs`. Jobs include a category, term, radius, enabled state, and one or more daily run times. The **System Logs** page at `/control-panel/system-logs` displays up to 250 recent Flask application log entries and can filter by severity. The logging handler stores `INFO` and higher records, including source location and exception details, in the `system_logs` SQLite table.

Start the scheduler separately with `python scheduler.py` for configured jobs to run.

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