from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.scrapers.craigslist import run_scraper as clscraper

# Define the new blueprint for control panel features
bp = Blueprint('control', __name__)

@bp.route('/control-panel', methods=('GET', 'POST'))
@login_required  # Optional: ensure user is authenticated
def control_panel():
    db = get_db()
    
    if request.method == 'POST' and 'craigslist_query' in request.form:
        query = request.form.get('craigslist_query', '').strip()
        radius = request.form.get('radius', 100)
        
        if query:
            # 1. Store search task
            db.execute(
                'INSERT INTO search_query (term, radius, status, created)'
                ' VALUES (?, ?, "completed", datetime("now"))',
                (query, radius)
            )
            db.commit()

            # 2. Immediately execute the scraper for this query
            clscraper(query=query)

            flash(f"Scraped and fetched posts for: '{query}'!", 'success')
            return redirect(url_for('control.control_panel'))

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