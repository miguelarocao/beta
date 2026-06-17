# Database Schema

SQLite database at `data/climbing.db`. Imported from Google Sheets ("Climbing Data Long") via `src/beta/import_sheets.py`.

## `climbs`

One row per grade per session. Multiple rows can share the same date.

| Column | Type | Description |
|---|---|---|
| `date` | TEXT | ISO date (YYYY-MM-DD) |
| `v_grade_raw` | TEXT | Raw grade from sheet, e.g. `"V5"` or `"V4-5"` for slash grades |
| `v_grade` | INTEGER | Resolved integer grade. Ranges like V4-5 are randomly sampled to a single int, seeded by date (deterministic but approximate) |
| `count` | INTEGER | Number of times this climb was done ("Count Multiplier") |
| `multiplier_attempts` | INTEGER | Total attempts including the send ("Attempts w/ send") |
| `sent` | INTEGER | 1 if the climb was sent, 0 if not |

## `sessions`

One row per training day. All time columns are in **minutes**.

| Column | Type | Description |
|---|---|---|
| `date` | TEXT | ISO date (YYYY-MM-DD), primary key |
| `workout_type` | TEXT | e.g. `"climbing"`, `"hangboard"` |
| `warmup` | INTEGER | Warmup time (minutes) |
| `climbing_time` | INTEGER | Time spent climbing (minutes) |
| `conditioning` | INTEGER | Conditioning time (minutes) |
| `stretch` | INTEGER | Stretching time (minutes) |
| `hang` | INTEGER | Hangboard time (minutes) |
| `other` | INTEGER | Other activity time (minutes) |
| `total_time` | INTEGER | Total session time (minutes) |

## `outdoor_climbs`

One row per outdoor bouldering day, recording where you climbed.

| Column | Type | Description |
|---|---|---|
| `date` | TEXT | ISO date (YYYY-MM-DD), primary key (one row per date) |
| `crag` | TEXT | Name of the crag / outdoor location |

## Notes

- `v_grade` for slash grades (e.g. V4-5) uses a seeded random — prefer `v_grade_raw` when precision matters
- Session time columns always sum to `total_time`
