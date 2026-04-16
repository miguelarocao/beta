"""Tool definitions for the BETA agent."""

import json
import sqlite3
from pathlib import Path
import vl_convert as vlc
from beta.display import imgcat

DB_PATH = Path(__file__).parent.parent.parent / "data" / "climbing.db"
ROW_LIMIT = 50

TOOLS = [
    {
        "name": "sql",
        "description": "Run a read-only SQL query against the climbing database. Tables: climbs (date, v_grade_raw, v_grade, count, multiplier_attempts, sent), sessions (date, workout_type, warmup, climbing_time, conditioning, stretch, hang, other, total_time), outdoor_climbs (date, v_grade_raw, v_grade, name, style).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_chart",
        "description": "Render a Vega-Lite chart. This can only be called after the sql tool has been invoked to fetch data. Pass a complete Vega-Lite spec including inline data values.",
        "input_schema": {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "object",
                    "description": "A complete Vega-Lite spec (https://vega.github.io/vega-lite/docs/). Must include '$schema', 'data' (with inline 'values'), and 'mark'/'encoding'.",
                },
            },
            "required": ["spec"],
        },
    },
    {
        "name": "clarify",
        "description": "Ask the user a clarifying question when the request is ambiguous.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The clarifying question to ask the user",
                },
            },
            "required": ["question"],
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    """Execute a tool and return the result as a string."""
    tool = {
        "sql": _handle_sql,
        "create_chart": _handle_create_chart,
        "clarify": _handle_clarify
    }
    fn = tool[name]
    return fn(args)

def _handle_sql(args: dict) -> str:
    """Execute a read-only SQL query."""
    # Open database in read-only mode - writes will fail at the SQLite level
    # TODO: should we only open this once?
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute(args["query"])
        rows = [dict(row) for row in cursor.fetchall()]
        if len(rows) > ROW_LIMIT:
            return f"ERROR: Too much data requested from DB ({len(rows)} rows). Preventing response to avoid high token usage."
        return json.dumps(rows, indent=2)
    except sqlite3.Error as e:
        return f"SQL error: {e}"
    finally:
        conn.close()


def _handle_create_chart(args: dict) -> str:
    """Create and display a chart."""
    try:
        png_data = vlc.vegalite_to_png(args["spec"])
        imgcat(png_data)
    except Exception as e:
        return f"Chart error: {e}"
    return "Chart displayed."


def _handle_clarify(args: dict) -> str:
    """Return the clarifying question to be shown to user."""
    return f"CLARIFY: {args['question']}"
