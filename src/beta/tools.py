"""Tool definitions for the BETA agent."""

import json
import sqlite3
from pathlib import Path
import altair as alt
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
        "description": "Create a chart visualization from data. This can only be called after the sql tool has been invoked to fetch data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of data objects to visualize",
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "scatter", "area"],
                    "description": "Type of chart to create",
                },
                "x": {
                    "type": "string",
                    "description": "Field to use for x-axis",
                },
                "y": {
                    "type": "string",
                    "description": "Field to use for y-axis",
                },
                "title": {
                    "type": "string",
                    "description": "Chart title",
                },
            },
            "required": ["data", "chart_type", "x", "y"],
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
    # TODO: This is probably too limiting

    data = alt.Data(values=args["data"])
    chart_type = args["chart_type"]

    # TODO: Generate and accept vega-lite JSON

    mark_map = {
        "bar": alt.Chart(data).mark_bar(color="#e85d04"),
        "line": alt.Chart(data).mark_line(color="#e85d04"),
        "scatter": alt.Chart(data).mark_circle(color="#e85d04"),
        "area": alt.Chart(data).mark_area(color="#e85d04"),
    }

    chart = mark_map[chart_type].encode(
        x=alt.X(f"{args['x']}:N"),
        y=alt.Y(f"{args['y']}:Q"),
    ).properties(
        title=args.get("title", ""),
        width=800,
        height=400,
    )

    png_data = vlc.vegalite_to_png(chart.to_dict())
    imgcat(png_data)

    return "Chart displayed."


def _handle_clarify(args: dict) -> str:
    """Return the clarifying question to be shown to user."""
    return f"CLARIFY: {args['question']}"
