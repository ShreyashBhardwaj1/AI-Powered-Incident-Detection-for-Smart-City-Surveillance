"""
backend/database.py
Cloud-compatible database layer.

Supports two backends selected by environment variable DATABASE_URL:

  LOCAL (default):
      SQLite — no setup needed, file stored at incidents.db
      DATABASE_URL not set  →  uses SQLite automatically

  CLOUD (set DATABASE_URL to any of these):
      PostgreSQL  — DATABASE_URL=postgresql://user:pass@host:5432/dbname
      Supabase    — DATABASE_URL=postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres
      Railway     — DATABASE_URL=postgresql://...  (auto-injected by Railway)
      Neon        — DATABASE_URL=postgresql://...  (auto-injected by Neon)
      Any other PostgreSQL-compatible service

Install for cloud:
    pip install psycopg2-binary        # standard PostgreSQL
    # OR
    pip install psycopg2               # if binary fails
"""

import os
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Detect backend ────────────────────────────────────────────────────────────
def _is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql://") or \
           DATABASE_URL.startswith("postgres://")


def _get_pg_conn():
    """Return a psycopg2 connection. Raises ImportError if not installed."""
    try:
        import psycopg2
    except ImportError:
        raise ImportError(
            "psycopg2 is required for PostgreSQL/cloud databases.\n"
            "Run:  pip install psycopg2-binary"
        )
    url = DATABASE_URL
    # Neon / some providers use 'postgres://' — psycopg2 needs 'postgresql://'
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url, sslmode="require")


def _get_sqlite_conn():
    """Return a sqlite3 connection to the local incidents.db file."""
    return sqlite3.connect("incidents.db")


# ── Public API ────────────────────────────────────────────────────────────────

def init_db():
    """
    Create the incidents table if it does not already exist.
    Safe to call on every startup.
    """
    if _is_postgres():
        conn = _get_pg_conn()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id            SERIAL PRIMARY KEY,
                incident_type VARCHAR(100)  NOT NULL,
                severity      VARCHAR(50)   NOT NULL,
                latitude      DOUBLE PRECISION NOT NULL,
                longitude     DOUBLE PRECISION NOT NULL,
                timestamp     TIMESTAMP     NOT NULL DEFAULT NOW(),
                confidence    DOUBLE PRECISION,
                raw_label     VARCHAR(100)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[database] PostgreSQL table ready.")
    else:
        conn = _get_sqlite_conn()
        conn.execute("DROP TABLE IF EXISTS incidents")   
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT    NOT NULL,
                severity      TEXT    NOT NULL,
                latitude      REAL    NOT NULL,
                longitude     REAL    NOT NULL,
                timestamp     TEXT    NOT NULL,
                confidence    REAL,
                raw_label     TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("[database] SQLite table ready.")


def insert_incident(
    incident_type: str,
    severity:      str,
    lat:           float,
    lon:           float,
    timestamp:     str,
    confidence:    float = None,
    raw_label:     str   = None,
) -> int:
    """
    Insert a new incident record.
    Returns the new row ID.
    """
    if _is_postgres():
        conn = _get_pg_conn()
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO incidents
                (incident_type, severity, latitude, longitude, timestamp, confidence, raw_label)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (incident_type, severity, lat, lon, timestamp, confidence, raw_label)
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = _get_sqlite_conn()
        cur  = conn.execute(
            """
            INSERT INTO incidents
                (incident_type, severity, latitude, longitude, timestamp, confidence, raw_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (incident_type, severity, lat, lon, timestamp, confidence, raw_label)
        )
        row_id = cur.lastrowid
        conn.commit()
        conn.close()

    print(f"[database] Incident saved (id={row_id}): {incident_type} | {severity}")
    return row_id


def get_all_incidents(limit: int = 100) -> list[dict]:
    """
    Retrieve the most recent incidents (latest first).
    Useful for a dashboard or analytics endpoint.
    """
    if _is_postgres():
        conn = _get_pg_conn()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, incident_type, severity, latitude, longitude, timestamp, confidence, raw_label "
            "FROM incidents ORDER BY timestamp DESC LIMIT %s",
            (limit,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    else:
        conn = _get_sqlite_conn()
        cur  = conn.execute(
            "SELECT id, incident_type, severity, latitude, longitude, timestamp, confidence, raw_label "
            "FROM incidents ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        conn.close()

    return [
        {
            "id":            r[0],
            "incident_type": r[1],
            "severity":      r[2],
            "latitude":      r[3],
            "longitude":     r[4],
            "timestamp":     str(r[5]),
            "confidence":    r[6],
            "raw_label":     r[7],
        }
        for r in rows
    ]