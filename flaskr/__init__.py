import os
import socket
from flask import Flask
import sqlite3
import click
import markupsafe
from flask import current_app, g
from flaskr.system_logging import install_database_logging
from flask.cli import with_appcontext


def create_app(test_config=None):
    hostname = socket.gethostname()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY'),
        GOOGLE_CLIENT_ID=os.environ.get('GOOGLE_CLIENT_ID'),
        GOOGLE_CLIENT_SECRET=os.environ.get('GOOGLE_CLIENT_SECRET'),
        CL_URL=os.environ.get('CL_URL', 'http://127.0.0.1:5001'),
        DATABASE='/home/jon/local/data/flaskr.sqlite',
    )
    if test_config is not None:
        app.config.update(test_config)

    install_database_logging(app)

    from . import db
    db.init_app(app)

    # Register custom nl2br filter
    @app.context_processor
    def inject_cl_url():
        return dict(cl_url=app.config['CL_URL'])

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
    auth.init_oauth(app)
    with app.app_context():
        auth.ensure_identity_schema()
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)

    from . import weather
    app.register_blueprint(weather.bp)

    from . import network
    app.register_blueprint(network.bp)
    
    from . import astronomy
    app.register_blueprint(astronomy.bp)

    # Register the new control blueprint
    from . import control
    app.register_blueprint(control.bp)

    # Point the root URL ('/') directly to the weather index view
    from .weather.routes import index
    app.add_url_rule('/', endpoint='index', view_func=index)

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
