"""Bounded SQLite connection pools with durable WAL and explicit cleanup."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading

from sqlalchemy import create_engine, event

_engines = {}
_lock = threading.Lock()


def configure_sqlite_engine(engine):
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def pragmas(connection, record):
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA journal_mode=WAL")
            # Preserve commit durability; do not trade it away for benchmark speed.
            cursor.execute("PRAGMA synchronous=FULL")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


@contextmanager
def database_connection(path):
    key = str(Path(path).resolve())
    with _lock:
        if key not in _engines:
            engine = create_engine("sqlite:///"+key.replace("\\", "/"),
                                   pool_size=16, max_overflow=0, pool_timeout=30,
                                   connect_args={"timeout": 30, "check_same_thread": False})
            configure_sqlite_engine(engine)
            _engines[key] = engine
        engine = _engines[key]
    pooled = engine.raw_connection()
    connection = pooled.driver_connection
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        # Return the handle even if a caller rolls back or raises.
        pooled.close()
