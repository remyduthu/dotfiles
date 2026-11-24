---
name: turin-toulouse
description: >-
  Turin ↔ Toulouse trip planner, either direction. Use when I ask how to travel between
  Turin and Toulouse, or to recheck or calendar a trip it planned.
---

# Turin ↔ Toulouse

I travel this **corridor** often. A good trip: a good night before, a long day with
**pauses** to read (I can't read on a bus or train), roomy connections, no night bus.
`scripts/trip.py` holds these preferences as numbers, budget included; trip.json
overrides them only when I say so.

Run the script as `uv run <base directory of this skill>/scripts/trip.py`; `--help` lists
its commands. `tests/fixture.json` and `tests/selection.json` are complete examples of the
files you write.

`<base directory of this skill>/trips/` is the corridor's **memory**, local and ignored
by git: one **trip folder** per trip (`<date>-<direction>/`, every file of that trip),
and `lessons.md`, what past trips taught.

## Phases

Read each phase file when you enter it, and finish its steps before the next phase.

1. **Collect** ([COLLECT.md](COLLECT.md)): the sites' legs into trip.json.
2. **Analyze** ([ANALYZE.md](ANALYZE.md)): itineraries, then the options worth showing.
3. **Report** ([REPORT.md](REPORT.md)): the comparison page, and everything after it.
