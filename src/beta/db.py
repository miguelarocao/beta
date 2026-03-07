"""SQLite database connection and helpers."""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "climbing.db"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create tables if they don't exist."""
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.executescript("""
        DROP TABLE IF EXISTS climbs;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS outdoor_climbs;

        CREATE TABLE climbs (
            date TEXT NOT NULL,
            v_grade_raw TEXT NOT NULL,
            v_grade INTEGER NOT NULL,
            count INTEGER NOT NULL,
            multiplier_attempts INTEGER NOT NULL,
            sent INTEGER NOT NULL
        );

        CREATE TABLE sessions (
            date TEXT PRIMARY KEY,
            workout_type TEXT,
            warmup INTEGER,
            climbing_time INTEGER,
            conditioning INTEGER,
            stretch INTEGER,
            hang INTEGER,
            other INTEGER,
            total_time INTEGER
        );

        CREATE TABLE outdoor_climbs (
            date TEXT NOT NULL,
            v_grade_raw TEXT NOT NULL,
            v_grade INTEGER NOT NULL,
            name TEXT,
            style TEXT
        );

        CREATE INDEX idx_climbs_date ON climbs(date);
        CREATE INDEX idx_outdoor_climbs_date ON outdoor_climbs(date);
    """)
    conn.commit()
    conn.close()
