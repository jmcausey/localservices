import socket
import sqlite3
import threading
import pandas as pd
from flask import Blueprint, render_template, request, jsonify
from flaskr.db import get_db
from scapy.all import IP, TCP, sniff

# Only define the blueprint once
bp = Blueprint('network', __name__)
hostname = socket.gethostname()

@bp.route('/')
@bp.route('/network')
def network():
  db = get_db()

  # 1. Fetch rows from SQLite (including the timestamp for context)
  cursor = db.execute('''
        SELECT timestamp, source_ip, source_port, dest_ip, dest_port, protocol, status, message 
        FROM network_logs 
        ORDER BY timestamp DESC
    ''')
  rows = cursor.fetchall()

  # 2. Get column names from the cursor description
  columns = [description[0] for description in cursor.description]

  # 3. Convert rows into standard dictionaries for a clean DataFrame load
  data = [dict(row) for row in rows]
  df = pd.DataFrame(data, columns=columns)

  # 4. Convert DataFrame to a styled HTML table string
  html_table = df.to_html(
      classes='table table-striped network-table', index=False
  )

  return render_template('network.html', table=html_table, hostname=hostname)
