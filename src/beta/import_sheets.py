"""Import climbing data from Google Sheets into SQLite."""

import os
import random
import re
import sqlite3
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from beta.db import DEFAULT_DB_PATH, init_db

SPREADSHEET_NAME = "Climbing Data Long"

EXPECTED_CLIMB_HEADERS = ["Date", "V Grade", "Count Multiplier", "Attempts (w/ send)", "Sent"]
EXPECTED_SESSION_HEADERS = [
    "Date", "workout type", "warmup", "climbing time",
    "conditioning", "stretch", "hang", "other", "total time"
]
EXPECTED_OUTDOOR_HEADERS = ["Climb name", "V Grade", "Style", "Date"]


class HeaderMismatchError(Exception):
    """Raised when sheet headers don't match expected columns."""


DEFAULT_CREDS_PATH = Path(__file__).parent.parent.parent / "service-account.json"


def get_sheets_client() -> gspread.Client:
    """Create authenticated gspread client from service account."""
    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_path:
        if DEFAULT_CREDS_PATH.exists():
            creds_path = str(DEFAULT_CREDS_PATH)
        else:
            raise EnvironmentError(
                "No service account found. Either set GOOGLE_SERVICE_ACCOUNT_JSON "
                "or place service-account.json in the project root."
            )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(creds)


def validate_headers(actual: list[str], expected: list[str], sheet_name: str) -> None:
    """Raise if headers don't match expected columns."""
    actual_clean = [h.strip() for h in actual[:len(expected)]]
    if actual_clean != expected:
        raise HeaderMismatchError(
            f"{sheet_name}: expected headers {expected}, got {actual_clean}"
        )


def resolve_grade(grade_raw: str, date_seed: str) -> int:
    """Resolve grade like 'V4-5' to single int using seeded random."""
    grade_raw = grade_raw.strip().upper()

    # Handle range grades like "V4-5" or "V3-4"
    range_match = re.match(r"V(\d+)-(\d+)", grade_raw)
    if range_match:
        low, high = int(range_match.group(1)), int(range_match.group(2))
        rng = random.Random(f"{date_seed}:{grade_raw}")
        return rng.randint(low, high)

    # Handle single grades like "V5"
    single_match = re.match(r"V(\d+)", grade_raw)
    if single_match:
        return int(single_match.group(1))

    # Fallback for unparseable grades
    return 0


def parse_date(date_str: str) -> str:
    """Convert DD/MM/YYYY to YYYY-MM-DD."""
    parts = date_str.strip().split("/")
    if len(parts) == 3:
        day, month, year = parts
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str


def parse_int(val: str, default: int = 0) -> int:
    """Parse string to int, returning default on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def parse_bool(val: str) -> int:
    """Parse boolean string to 0/1."""
    return 1 if str(val).strip().upper() == "TRUE" else 0


def fetch_climbs(client: gspread.Client) -> list[dict]:
    """Fetch and transform indoor climb data."""
    spreadsheet = client.open(SPREADSHEET_NAME)
    # Try named range first, fall back to first sheet
    try:
        data = spreadsheet.values_get("raw_climb_data")["values"]
    except gspread.exceptions.APIError:
        ws = spreadsheet.sheet1
        data = ws.get_all_values()

    if not data:
        return []

    validate_headers(data[0], EXPECTED_CLIMB_HEADERS, "climbs")

    rows = []
    for row in data[1:]:
        if len(row) < 5 or not row[0].strip():
            continue

        date = parse_date(row[0])
        v_grade_raw = row[1].strip()
        v_grade = resolve_grade(v_grade_raw, date)
        count = parse_int(row[2], default=1)
        multiplier_attempts = parse_int(row[3], default=1)
        sent = parse_bool(row[4])

        rows.append({
            "date": date,
            "v_grade_raw": v_grade_raw,
            "v_grade": v_grade,
            "count": count,
            "multiplier_attempts": multiplier_attempts,
            "sent": sent,
        })

    return rows


def fetch_sessions(client: gspread.Client) -> list[dict]:
    """Fetch and transform session data."""
    spreadsheet = client.open(SPREADSHEET_NAME)
    try:
        data = spreadsheet.values_get("raw_session_data")["values"]
    except gspread.exceptions.APIError:
        # Fall back to second sheet
        ws = spreadsheet.get_worksheet(1)
        if ws is None:
            return []
        data = ws.get_all_values()

    if not data:
        return []

    validate_headers(data[0], EXPECTED_SESSION_HEADERS, "sessions")

    rows = []
    for row in data[1:]:
        if len(row) < 9 or not row[0].strip():
            continue

        date = parse_date(row[0])
        rows.append({
            "date": date,
            "workout_type": row[1].strip() if len(row) > 1 else None,
            "warmup": parse_int(row[2]) if len(row) > 2 else 0,
            "climbing_time": parse_int(row[3]) if len(row) > 3 else 0,
            "conditioning": parse_int(row[4]) if len(row) > 4 else 0,
            "stretch": parse_int(row[5]) if len(row) > 5 else 0,
            "hang": parse_int(row[6]) if len(row) > 6 else 0,
            "other": parse_int(row[7]) if len(row) > 7 else 0,
            "total_time": parse_int(row[8]) if len(row) > 8 else 0,
        })

    return rows


def fetch_outdoor(client: gspread.Client) -> list[dict]:
    """Fetch and transform outdoor climb data."""
    spreadsheet = client.open(SPREADSHEET_NAME)
    # Outdoor data is typically on a separate sheet
    try:
        ws = spreadsheet.worksheet("Outdoor Bouldering")
    except gspread.exceptions.WorksheetNotFound:
        return []

    data = ws.get_all_values()
    if not data:
        return []

    validate_headers(data[0], EXPECTED_OUTDOOR_HEADERS, "outdoor_climbs")

    rows = []
    for row in data[1:]:
        if len(row) < 4 or not row[0].strip():
            continue

        name = row[0].strip()
        v_grade_raw = row[1].strip()
        style = row[2].strip() if len(row) > 2 else None
        date = parse_date(row[3]) if len(row) > 3 else None

        if not date:
            continue

        v_grade = resolve_grade(v_grade_raw, date)

        rows.append({
            "date": date,
            "v_grade_raw": v_grade_raw,
            "v_grade": v_grade,
            "name": name,
            "style": style,
        })

    return rows


def upsert_climbs(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Insert climb rows (delete-insert for simplicity)."""
    conn.execute("DELETE FROM climbs")
    conn.executemany(
        """INSERT INTO climbs (date, v_grade_raw, v_grade, count, multiplier_attempts, sent)
           VALUES (:date, :v_grade_raw, :v_grade, :count, :multiplier_attempts, :sent)""",
        rows,
    )
    return len(rows)


def upsert_sessions(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Insert session rows (replace on conflict)."""
    conn.execute("DELETE FROM sessions")
    conn.executemany(
        """INSERT INTO sessions (date, workout_type, warmup, climbing_time,
                                 conditioning, stretch, hang, other, total_time)
           VALUES (:date, :workout_type, :warmup, :climbing_time,
                   :conditioning, :stretch, :hang, :other, :total_time)""",
        rows,
    )
    return len(rows)


def upsert_outdoor(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Insert outdoor climb rows."""
    conn.execute("DELETE FROM outdoor_climbs")
    conn.executemany(
        """INSERT INTO outdoor_climbs (date, v_grade_raw, v_grade, name, style)
           VALUES (:date, :v_grade_raw, :v_grade, :name, :style)""",
        rows,
    )
    return len(rows)


def import_all(db_path: Path | None = None) -> dict[str, int]:
    """Import all data from Google Sheets into SQLite.

    Returns dict with row counts per table.
    """
    path = db_path or DEFAULT_DB_PATH
    init_db(path)

    client = get_sheets_client()

    climbs = fetch_climbs(client)
    sessions = fetch_sessions(client)
    outdoor = fetch_outdoor(client)

    conn = sqlite3.connect(path)
    try:
        counts = {
            "climbs": upsert_climbs(conn, climbs),
            "sessions": upsert_sessions(conn, sessions),
            "outdoor_climbs": upsert_outdoor(conn, outdoor),
        }
        conn.commit()
    finally:
        conn.close()

    return counts
