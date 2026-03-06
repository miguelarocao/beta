# BETA: Better Exploration of Training Analytics

CLI agent for natural language queries on climbing data. Intentionally over-engineered — the goal is learning agent internals (tool orchestration, loop logic, error handling, evaluation), not just working code.

## Architecture (V0)

```
CLI input → Agent (Claude API)
              ├── query_climbs(filters, aggregations)
              ├── query_sessions(filters, aggregations)
              ├── create_chart(data, chart_type, options)
              └── clarify(question)
           → Print response / display chart
```

Single agent, raw Anthropic API (no framework).

## Data

SQLite tables:
- **climbs**: date, v_grade, count, multiplier_attempts, sent
- **sessions**: date, workout_type, warmup, climbing_time, conditioning, stretch, hang, other, total_time

## Working Agreement

**Core rule:** Do NOT implement core agent logic directly (agent loop, tool dispatch, stop conditions, retry/clarify logic). Instead:
- Explain the approach and tradeoffs
- Ask clarifying questions
- Use `TODO(human)` markers for Miguel to implement

**Do implement directly:** Boilerplate, chart generation, test harness, refactoring.

## Git

Conventional commits with short titles (<50 chars). Details go in the body as bullet points.

## Design Decisions

- Structured query tools over raw SQL (safer, better for learning interface design)
- Single agent first, multi-agent later
- CLI/REPL only (no UI)
- Altair for charts
