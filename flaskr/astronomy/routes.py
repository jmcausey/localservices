import os
import sqlite3
from flask import Blueprint, render_template

DATABASE = os.path.expanduser('~/local/data/flaskr.sqlite')

bp = Blueprint('astronomy', __name__)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name: row['city']
    return conn


@bp.route('/astronomy')
def astronomy_table():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM astronomy ORDER BY timestamp DESC').fetchall()
    conn.close()
    
    return render_template('astronomy.html', records=records)