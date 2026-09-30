from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.craigslist_categories import CRAIGSLIST_CATEGORIES, CRAIGSLIST_CATEGORY_GROUPS
from flaskr.db import get_db

# Define the new blueprint for control panel features
bp = Blueprint('control', __name__)

@bp.route('/control-panel', methods=('GET', 'POST'))
@login_required  # Optional: ensure user is authenticated
def control_panel():
    db = get_db()

    # Extract Blog Filtering Options from Query Strings
    status_filter = request.args.get('status', 'all')
    search_keyword = request.args.get('q', '').strip()
    age_filter = request.args.get('age', 'all')

    # Construct Dynamic SQL Query for Filtered Posts
    sql = 'SELECT p.id, title, body, status, created, author_id, username' \
          ' FROM post p JOIN user u ON p.author_id = u.id WHERE 1=1'
    params = []

    if status_filter != 'all':
        sql += ' AND status = ?'
        params.append(status_filter)

    if search_keyword:
        sql += ' AND (title LIKE ? OR body LIKE ?)'
        params.extend([f'%{search_keyword}%', f'%{search_keyword}%'])

    if age_filter == '1day':
        sql += " AND datetime(created) >= datetime('now', '-1 day')"
    elif age_filter == '7days':
        sql += " AND datetime(created) >= datetime('now', '-7 days')"

    sql += ' ORDER BY created DESC'
    
    filtered_posts = db.execute(sql, params).fetchall()

    return render_template(
        'blog/control_panel.html',
        posts=filtered_posts,
        status_filter=status_filter,
        search_keyword=search_keyword,
        age_filter=age_filter
    )


def _job_form_values(form):
    name = form.get('name', '').strip()
    term = form.get('term', '').strip()
    category = form.get('category', '').strip()
    location_name = form.get('location_name', '').strip()
    location_url = form.get('location_url', '').strip().rstrip('/')
    if not name or not term:
        raise ValueError('Job name and search term are required.')
    if category not in CRAIGSLIST_CATEGORIES:
        raise ValueError('Choose a valid Craigslist category.')
    parsed_location = urlparse(location_url)
    hostname = (parsed_location.hostname or '').lower()
    is_area_url = parsed_location.path.startswith('/search/area/')
    if (
        not location_name
        or parsed_location.scheme != 'https'
        or not (hostname == 'craigslist.org' or hostname.endswith('.craigslist.org'))
        or parsed_location.username
        or parsed_location.password
        or (hostname in {'craigslist.org', 'www.craigslist.org'} and not is_area_url)
    ):
        raise ValueError('Enter a location name and a valid HTTPS Craigslist region URL.')
    if not is_area_url:
        location_url = f"{parsed_location.scheme}://{parsed_location.netloc}"
    else:
        location_url = f"{parsed_location.scheme}://{parsed_location.netloc}{parsed_location.path.rstrip('/')}"

    try:
        radius = int(form.get('radius', '100'))
    except ValueError as error:
        raise ValueError('Radius must be a number between 5 and 500.') from error
    if not 5 <= radius <= 500:
        raise ValueError('Radius must be between 5 and 500.')

    run_times = set()
    for value in form.get('run_times', '').split(','):
        value = value.strip()
        if not value:
            continue
        try:
            run_times.add(datetime.strptime(value, '%H:%M').strftime('%H:%M'))
        except ValueError as error:
            raise ValueError('Run times must use HH:MM, separated by commas.') from error
    if not run_times:
        raise ValueError('Add at least one daily run time in HH:MM format.')

    return (
        name,
        term,
        category,
        radius,
        ','.join(sorted(run_times)),
        location_name,
        location_url,
    )


@bp.route('/control-panel/cl-jobs', methods=('GET', 'POST'))
@login_required
def craigslist_jobs():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            try:
                job_id = int(request.form.get('job_id', ''))
            except ValueError:
                abort(400)

            job = db.execute(
                'SELECT job_key, name, is_default_location '
                'FROM craigslist_jobs WHERE id = ?',
                (job_id,),
            ).fetchone()
            if job is None:
                abort(404)
            db.execute('DELETE FROM craigslist_jobs WHERE id = ?', (job_id,))
            if job['is_default_location']:
                fallback = db.execute(
                    "SELECT id FROM craigslist_jobs "
                    "ORDER BY CASE WHEN job_key = 'pets' THEN 0 ELSE 1 END, id "
                    "LIMIT 1"
                ).fetchone()
                if fallback:
                    db.execute(
                        'UPDATE craigslist_jobs SET is_default_location = 1 WHERE id = ?',
                        (fallback['id'],),
                    )
            db.commit()
            flash(f"Deleted Craigslist search job '{job['name']}'.", 'success')
            return redirect(url_for('control.craigslist_jobs'))

        try:
            (
                name,
                term,
                category,
                radius,
                run_times,
                location_name,
                location_url,
            ) = _job_form_values(request.form)
        except ValueError as error:
            flash(str(error), 'error')
            return redirect(url_for('control.craigslist_jobs'))

        enabled = 1 if request.form.get('enabled') == 'on' else 0
        is_default_location = 1 if request.form.get('is_default_location') == 'on' else 0
        if is_default_location:
            db.execute('UPDATE craigslist_jobs SET is_default_location = 0')
        if action == 'add':
            db.execute(
                'INSERT INTO craigslist_jobs '
                '(job_key, name, term, category, radius, run_times, location_name, '
                'location_url, is_default_location, enabled) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    uuid4().hex,
                    name,
                    term,
                    category,
                    radius,
                    run_times,
                    location_name,
                    location_url,
                    is_default_location,
                    enabled,
                ),
            )
            flash(f"Added Craigslist search job '{name}'.", 'success')
        elif action == 'update':
            try:
                job_id = int(request.form.get('job_id', ''))
            except ValueError:
                abort(400)
            cursor = db.execute(
                'UPDATE craigslist_jobs SET name = ?, term = ?, category = ?, '
                'radius = ?, run_times = ?, location_name = ?, location_url = ?, '
                'is_default_location = ?, enabled = ?, '
                'updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (
                    name,
                    term,
                    category,
                    radius,
                    run_times,
                    location_name,
                    location_url,
                    is_default_location,
                    enabled,
                    job_id,
                ),
            )
            if cursor.rowcount == 0:
                abort(404)
            flash(f"Updated Craigslist search job '{name}'.", 'success')
        else:
            abort(400)

        db.commit()
        return redirect(url_for('control.craigslist_jobs'))

    jobs = db.execute(
        'SELECT id, name, term, category, radius, run_times, location_name, '
        'location_url, is_default_location, enabled, last_run_at '
        'FROM craigslist_jobs ORDER BY enabled DESC, name COLLATE NOCASE'
    ).fetchall()
    default_location = db.execute(
        'SELECT location_name, location_url FROM craigslist_jobs '
        'WHERE is_default_location = 1 LIMIT 1'
    ).fetchone()
    return render_template(
        'blog/craigslist_jobs.html',
        jobs=jobs,
        category_groups=CRAIGSLIST_CATEGORY_GROUPS,
        default_location=default_location,
    )


@bp.route('/control-panel/system-logs')
@login_required
def system_logs():
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    level_filter = request.args.get('level', 'all').upper()
    if level_filter != 'ALL' and level_filter not in levels:
        level_filter = 'ALL'

    db = get_db()
    if level_filter == 'ALL':
        logs = db.execute(
            'SELECT id, created_at, level, logger, message, pathname, '
            'line_number, exception FROM system_logs '
            'ORDER BY created_at DESC, id DESC LIMIT 250'
        ).fetchall()
    else:
        logs = db.execute(
            'SELECT id, created_at, level, logger, message, pathname, '
            'line_number, exception FROM system_logs WHERE level = ? '
            'ORDER BY created_at DESC, id DESC LIMIT 250',
            (level_filter,)
        ).fetchall()

    return render_template(
        'blog/system_logs.html',
        logs=logs,
        level_filter=level_filter,
        levels=levels,
    )