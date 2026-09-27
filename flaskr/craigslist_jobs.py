from datetime import datetime
from urllib.parse import quote_plus

from flaskr.scrapers.craigslist import PET_SEARCH_URL, run_scraper


def execute_craigslist_job(job):
    category = job["category"]
    area_label = "East Texas" if category in {"pet", "zip"} else "100 miles of Athens, TX"
    search_url = None
    if category == "pet":
        search_url = PET_SEARCH_URL.split("#", 1)[0]
        if job["term"].strip().lower() != "pets":
            search_url += f"&query={quote_plus(job['term'])}"
    return run_scraper(
        query=job["term"],
        max_results=None,
        search_url=search_url,
        category=category,
        area_label=area_label,
        radius=job["radius"],
    )


def run_due_craigslist_jobs(db, now=None, force=False, runner=execute_craigslist_job):
    now = now or datetime.now()
    jobs = db.execute(
        "SELECT * FROM craigslist_jobs WHERE enabled = 1 ORDER BY id"
    ).fetchall()
    runs = 0

    for job in jobs:
        run_times = [value.strip() for value in job["run_times"].split(",") if value.strip()]
        if force:
            run_times = [now.strftime("%H:%M")]

        for run_time in run_times:
            try:
                scheduled_time = datetime.strptime(run_time, "%H:%M").time()
            except ValueError:
                continue

            scheduled_at = now.replace(
                hour=scheduled_time.hour,
                minute=scheduled_time.minute,
                second=0,
                microsecond=0,
            )
            if not force and scheduled_at > now:
                continue

            last_run = job["last_run_at"]
            if last_run:
                try:
                    last_run_at = datetime.fromisoformat(last_run)
                except ValueError:
                    last_run_at = None
                if last_run_at and last_run_at >= scheduled_at:
                    continue

            db.execute(
                "UPDATE craigslist_jobs SET last_run_at = ?, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (scheduled_at.isoformat(sep=" "), job["id"]),
            )
            history = db.execute(
                "INSERT INTO search_query (term, radius, status, created) "
                "VALUES (?, ?, 'running', ?)",
                (job["term"], job["radius"], scheduled_at.isoformat(sep=" ")),
            )
            db.commit()

            try:
                runner(dict(job))
            except Exception as error:
                db.execute(
                    "UPDATE search_query SET status = 'failed' WHERE id = ?",
                    (history.lastrowid,),
                )
                db.commit()
                print(f"Craigslist job '{job['name']}' failed: {error}")
            else:
                db.execute(
                    "UPDATE search_query SET status = 'completed' WHERE id = ?",
                    (history.lastrowid,),
                )
                db.commit()
            runs += 1

    return runs