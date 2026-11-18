"""Opt-in local performance evidence; no bodies, tokens, or SQL text are logged."""
import json
import os
from pathlib import Path
import threading
import time

from flask import g, has_request_context, request
from sqlalchemy import event


def install_monitoring(app, db):
    path = Path(os.environ["APP_METRICS_FILE"]).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()

    @app.before_request
    def begin():
        g.perf_start = time.perf_counter()
        g.perf_sql_count = 0
        g.perf_sql_ms = 0.0

    @app.after_request
    def record(response):
        row = {
            "timestamp_ms": round(time.time() * 1000),
            "method": request.method,
            "route": str(request.url_rule or "unmatched"),
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - g.perf_start) * 1000, 3),
            "orm_sql_count": g.perf_sql_count,
            "orm_sql_ms": round(g.perf_sql_ms, 3),
        }
        with lock, path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        return response

    def before_sql(conn, cursor, statement, parameters, context, executemany):
        context.perf_started = time.perf_counter()

    def after_sql(conn, cursor, statement, parameters, context, executemany):
        if has_request_context():
            g.perf_sql_count = getattr(g, "perf_sql_count", 0) + 1
            g.perf_sql_ms = getattr(g, "perf_sql_ms", 0.0) + (time.perf_counter() - context.perf_started) * 1000

    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", before_sql)
        event.listen(db.engine, "after_cursor_execute", after_sql)
