import logging
import sqlite3

from flask import current_app, has_app_context


CREATE_SYSTEM_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    logger TEXT NOT NULL,
    message TEXT NOT NULL,
    pathname TEXT,
    line_number INTEGER,
    exception TEXT
)
"""


def ensure_system_logs_table(database_path):
    with sqlite3.connect(database_path) as connection:
        connection.execute(CREATE_SYSTEM_LOGS_TABLE)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_logs_created_at "
            "ON system_logs(created_at DESC)"
        )


class SQLiteLogHandler(logging.Handler):
    def __init__(self, database_path):
        super().__init__(level=logging.INFO)
        self.database_path = database_path
        self.setFormatter(logging.Formatter())

    def emit(self, record):
        try:
            database_path = (
                current_app.config["DATABASE"]
                if has_app_context()
                else self.database_path
            )
            exception = None
            if record.exc_info:
                exception = self.formatter.formatException(record.exc_info)

            with sqlite3.connect(database_path, timeout=5) as connection:
                connection.execute(
                    """
                    INSERT INTO system_logs
                        (level, logger, message, pathname, line_number, exception)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.levelname,
                        record.name,
                        record.getMessage(),
                        record.pathname,
                        record.lineno,
                        exception,
                    ),
                )
        except Exception:
            self.handleError(record)


def install_database_logging(app):
    ensure_system_logs_table(app.config["DATABASE"])

    logger = app.logger
    logger.setLevel(logging.INFO)
    if not any(
        getattr(handler, "_system_logs_handler", False)
        for handler in logger.handlers
    ):
        handler = SQLiteLogHandler(app.config["DATABASE"])
        handler._system_logs_handler = True
        logger.addHandler(handler)