import os
import socket
from flask import Flask
import sqlite3
import click
import markupsafe
from flask import current_app, g
from flask.cli import with_appcontext

def create_app(test_config=None):
    hostname = socket.gethostname()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='/home/jon/local/data/flaskr.sqlite',
    )

    from . import db
    db.init_app(app)

    # Register custom nl2br filter
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if not s:
            return ""
        return markupsafe.Markup(str(s).replace('\n', '<br>\n'))

    # In your app creation file (e.g., __init__.py or app.py)
    @app.context_processor
    def inject_hostname():
        return dict(hostname=socket.gethostname())

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)

    from . import weather
    app.register_blueprint(weather.bp)

    from . import network
    app.register_blueprint(network.bp)
    
    from . import astronomy
    app.register_blueprint(astronomy.bp)

    # Point the root URL ('/') directly to the weather index view
    app.add_url_rule('/', endpoint='index', view_func=weather.index)

    return app

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

# ADD THIS NEW COMMAND HOOK BELOW
@click.command('scan-network')
@with_appcontext
def scan_network_command():
    """Run local network scanning routine and save live hosts."""
    from flaskr.scanner import run_network_scan
    run_network_scan()

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(scan_network_command) # Register it here
