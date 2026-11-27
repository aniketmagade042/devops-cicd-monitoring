"""Guestbook service used to practise CI/CD and monitoring.

Configuration comes only from environment variables:
  APP_ENV       development | staging | production
  SECRET_KEY    required in production
  DATABASE_URL  postgresql://user:pass@host:5432/db (default: local SQLite file)
  LOG_LEVEL     DEBUG | INFO | WARNING | ERROR
  APP_VERSION   build number, set by the pipeline
  GIT_SHA       commit that was built, set by the pipeline

Observability endpoints:
  /health   liveness + database check (used by Docker, CI and the uptime monitor)
  /version  which build is running
  /metrics  request counters in Prometheus text format
"""
import logging
import os
import sqlite3
import sys
import time
from collections import Counter
from contextlib import closing
from threading import Lock

from flask import (Flask, Response, flash, g, jsonify, redirect,
                   render_template, request, url_for)

APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "unknown")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///guestbook.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
PH = "%s" if USE_POSTGRES else "?"
QUIET_ENDPOINTS = {"health", "metrics"}

logger = logging.getLogger("guestbook")
logger.setLevel(LOG_LEVEL)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logger.addHandler(_handler)

app = Flask(__name__)
_secret = os.getenv("SECRET_KEY")
if not _secret:
    if APP_ENV == "production":
        raise RuntimeError("SECRET_KEY must be set in production")
    _secret = "dev-only-insecure-key"
    logger.warning("Using insecure development SECRET_KEY")
app.secret_key = _secret

START_TIME = time.time()
_request_counts = Counter()
_counter_lock = Lock()


def get_conn():
    if USE_POSTGRES:
        import psycopg2

        return psycopg2.connect(DATABASE_URL.replace("postgres://", "postgresql://", 1))
    return sqlite3.connect(DATABASE_URL.replace("sqlite:///", "", 1))


def init_db():
    pk = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS entries (id {pk}, name VARCHAR(60) NOT NULL, "
            f"message VARCHAR(280) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
    logger.info("Database ready (%s) version=%s sha=%s",
                "postgres" if USE_POSTGRES else "sqlite", APP_VERSION, GIT_SHA)


try:
    init_db()
except Exception:
    logger.exception("Database initialisation failed")


@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record_request(response):
    """Count every request and write one structured log line per request."""
    endpoint = request.endpoint or "unknown"
    duration_ms = (time.perf_counter() - g.get("start", time.perf_counter())) * 1000
    with _counter_lock:
        _request_counts[(endpoint, request.method, str(response.status_code))] += 1
    level = logging.DEBUG if endpoint in QUIET_ENDPOINTS else logging.INFO
    logger.log(level, "request method=%s endpoint=%s status=%d duration_ms=%.1f",
               request.method, endpoint, response.status_code, duration_ms)
    return response


@app.get("/")
def index():
    try:
        with closing(get_conn()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, message, created_at FROM entries ORDER BY id DESC LIMIT 50")
            entries = cur.fetchall()
    except Exception:
        logger.exception("Could not load entries")
        entries = []
        flash("Database is unavailable right now.")
    return render_template("index.html", entries=entries, env=APP_ENV, version=APP_VERSION)


@app.post("/sign")
def sign():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()
    if not (1 <= len(name) <= 60 and 1 <= len(message) <= 280):
        flash("Name (1-60 chars) and message (1-280 chars) are required.")
        return redirect(url_for("index"))
    try:
        with closing(get_conn()) as conn:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO entries (name, message) VALUES ({PH}, {PH})", (name, message))
            conn.commit()
        logger.info("New entry saved (name length=%d)", len(name))
        flash("Thanks for signing!")
    except Exception:
        logger.exception("Could not save entry")
        flash("Could not save your entry. Please try again.")
    return redirect(url_for("index"))


@app.get("/health")
def health():
    try:
        with closing(get_conn()) as conn:
            conn.cursor().execute("SELECT 1")
        return jsonify(status="ok", db="ok", env=APP_ENV)
    except Exception:
        logger.exception("Health check failed")
        return jsonify(status="error", db="down"), 503


@app.get("/version")
def version():
    return jsonify(version=APP_VERSION, git_sha=GIT_SHA, env=APP_ENV)


@app.get("/metrics")
def metrics():
    lines = [
        "# HELP guestbook_requests_total Total HTTP requests handled by this worker.",
        "# TYPE guestbook_requests_total counter",
    ]
    with _counter_lock:
        items = sorted(_request_counts.items())
    for (endpoint, method, status), count in items:
        lines.append(
            f'guestbook_requests_total{{endpoint="{endpoint}",method="{method}",'
            f'status="{status}"}} {count}'
        )
    lines += [
        "# HELP guestbook_uptime_seconds Seconds since this worker started.",
        "# TYPE guestbook_uptime_seconds gauge",
        f"guestbook_uptime_seconds {time.time() - START_TIME:.0f}",
        "# HELP guestbook_build_info Build information.",
        "# TYPE guestbook_build_info gauge",
        f'guestbook_build_info{{version="{APP_VERSION}",git_sha="{GIT_SHA}"}} 1',
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain; version=0.0.4")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=(APP_ENV == "development"))
