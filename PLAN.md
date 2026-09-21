# PLAN: Total hours per person

## Goal

Event names act as a person identifier (each event is a work shift). Add a new
table that sums the hours each person worked in the selected period: events with
the same name get their `duration_hours` added together.

## Decisions

- The aggregation is a **separate function** in the package, not mixed into
  `read_events`, so it stays reusable by the app and scripts.
- It operates on the already-filtered events, so ignored names (`CET opens`,
  `CET closes`) and out-of-range events never reach the sum.
- Result is sorted by total hours descending.
- Totals are rounded to 2 decimals.

## Changes

1. **`src/calendar_reader/__init__.py`**
   - Added `total_hours_by_person(events: list[dict]) -> list[dict]`.
   - Accumulates `duration_hours` in a dict keyed by `name`, then returns a list
     of `{"name": str, "total_hours": float}` sorted by `total_hours` descending.

2. **`app/streamlit_app.py`**
   - Imports `total_hours_by_person` next to `read_events`.
   - After a successful scan, shows two tables:
     - `Events` (the raw event list).
     - `Hours per person` (the aggregated totals).

3. **`README.md`**
   - Added an "Hours per person" section with a usage example and the return
     shape.

## Verification

- Temporary ICS with `Alice` (4 h + 2.5 h) and `Bob` (2 h) plus one `CET opens`:
  output was `Alice 6.5` then `Bob 2.0`, ignoring the `CET opens` event.
- Regression: `scripts/try_calendar.py` output unchanged.
- `app/streamlit_app.py` compiles.

## Out of scope

- Rounding/formatting options.
- Filtering or sorting controls in the UI.
