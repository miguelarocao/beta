# Plan: Semantic Layer for Faster Analytical Queries

**Status:** Designed, not started. Pick up later.

## Motivation

Answering questions like *"did my indoor climbing improve over time?"* repeatedly re-derives
the same domain logic in raw SQL. Friction observed while answering it:

- Re-deriving filters/semantics by hand on every question.
- Expanding `climbs` rows by `count` needed a recursive CTE that **exploded** (query killed,
  exit 144). Had to fall back to a numbers-table expansion.
- Reinventing top-k / quarter bucketing each time.
- `ROW_LIMIT=100` in `tools.py` can block large rollups.

Root cause: **the same domain knowledge is re-derived on every question.** That's the thing to
store — not the answers.

## Key decision: materialized `sends` table

Build a precomputed semantic layer at **import time** (`import_sheets.py`). Because the data is
**static** (one-time import from Google Sheets, never changes), materialize it as a real table —
no staleness risk, and queries become instant. This is the "Transform" step currently missing
from the import's Extract + Load.

### Proposed `sends` table

One row per **send-instance** (already expanded by `count`):

```sql
CREATE TABLE sends AS
SELECT
  c.date,
  c.v_grade,                                     -- use this directly (see grade decision)
  CAST(strftime('%Y', c.date) AS INT)          AS year,
  (CAST(strftime('%m', c.date) AS INT)-1)/3+1  AS quarter,
  strftime('%Y-%m', c.date)                    AS month
FROM climbs c
JOIN /* numbers 1..N */ seq ON seq.i <= c.count  -- expansion happens ONCE, here
WHERE c.sent = 1;
```

Then today's exploding query becomes trivial:

```sql
SELECT quarter, AVG(v_grade) FROM sends GROUP BY quarter;   -- top-k, percentiles all easy now
```

## Decisions settled (with evidence)

- **No `is_indoor` flag.** `climbs` has **0 rows on outdoor dates** — it is entirely indoor by
  construction. `outdoor_climbs` is a separate date+crag log with no grades. The earlier
  `WHERE date NOT IN (outdoor_climbs)` filter was a no-op.
- **Use `v_grade` directly; ignore `v_grade_raw` in general.** Slash grades (e.g. `V4-5`) are
  resolved by a **per-date seeded random** draw, which is **balanced/unbiased** — verified means
  land on midpoints (V2-3→2.50, V3-4→3.47, V4-5→4.43). For averages/trends this is correct and
  better than a deterministic floor/ceil (which would bias every slash grade downward). No
  deterministic-grade column needed.
  - **One caveat:** order statistics (`max`, top-k "ceiling" metrics) are *not* unbiased under
    random imputation — a `V5-7` rolling a 7 once can inflate the ceiling. Only for those metrics
    is it worth consulting `v_grade_raw` / flagging slash rows. Narrow exception, not a default.

## Implementation checklist (when resumed)

- [ ] Add `CREATE TABLE sends` step to `import_sheets.py` (count-expanded + year/quarter/month).
- [ ] **Discovery:** update the `sql` tool `description` in `tools.py` so the agent knows `sends`
      exists — otherwise it keeps querying `climbs` the hard way. (A derived table the agent
      doesn't know about is dead weight.)
- [ ] Document `sends` in `docs/database.md`.
- [ ] Revisit `ROW_LIMIT` — fine for aggregates, but confirm it doesn't block useful rollups.

## Open questions / TODOs

- [ ] **TODO(Miguel): provide a set of sample questions** the agent should make easy to answer.
      These drive which derived columns/metrics actually earn their place in `sends` (and whether
      a second rollup like `daily_summary` or a sessions/volume table is worth building). Without
      real target questions we risk over- or under-stuffing the table.
- [ ] Decide: materialized table vs. view. (Leaning materialized table given static data.)
- [ ] Consider a canonical "metrics cookbook" doc (ceiling/top-k, volume, etc.) as a companion —
      gives the agent vocabulary so it doesn't reinvent metrics. Lower priority than `sends`.

## Rejected alternatives

- **More tools:** not the bottleneck — the agent already has a full raw `sql` tool.
- **Answer/result cache (Q→A):** brittle (phrasings vary, won't string-match), can't be drilled
  into, and adds no value over never-stale views given static data.
