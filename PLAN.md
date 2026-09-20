# PLAN: ICS calendar reader tool

## Goal

Read an `.ics` file and, given two dates (`date_from`, `date_to`), return the
events within that range with the following data:

- Event name
- Date
- Start time
- End time
- Duration (in hours)

The result will be consumed by a manual test script and, in the future, by a
simple web app. That is why there is **no CLI**: the logic is exposed as a
reusable function.

## Settled decisions

- **ICS library:** `icalendar`, the only dependency. There are no recurring
  events (`RRULE`) or all-day events, so no extra libraries are needed.
- **No CLI:** the `[project.scripts]` entry point was removed from
  `pyproject.toml`.
- **Minimal code:** no dataclasses or unnecessary layers; an event is a flat
  `dict`.
- **Timezones:** the real `.ics` stores times in UTC (`Z`), even though the
  calendar is from Madrid. Times are converted to **`Europe/Madrid`** with
  `ZoneInfo("Europe/Madrid")` before filtering and displaying. On Windows,
  `tzdata` comes in as a dependency of `icalendar`, so nothing extra is added.
- **No automated tests at this stage:** validation is done with a manual script
  against a real `.ics`.

## Project rename

- Distribution name: **`calendar-reader`**.
- Package: **`calendar_reader`** (folder `src/calendar_reader/`).
- `pyproject.toml`: `name = "calendar-reader"`, no `[project.scripts]`, updated
  description.
- Lockfile regenerated with `uv lock`.

## Final structure

```
pyproject.toml
uv.lock
README.md
PLAN.md
src/
└── calendar_reader/
    └── __init__.py              # read_events() function
tests/
└── fixtures/
    └── test_calendar.ics        # real test calendar
scripts/
└── try_calendar.py              # manual dump script
```

- `tests/` is the folder `pytest` looks for; for now it only holds data under
  `tests/fixtures/`. Future tests will live as `tests/test_*.py`.
- `scripts/` holds development utilities meant to be run by hand.

## Public API

`src/calendar_reader/__init__.py`

```python
def read_events(path, date_from, date_to) -> list[dict]:
    ...
```

- `path`: `str | Path` to the `.ics` file.
- `date_from`, `date_to`: `datetime.date`.
- Returns a list of `dict`, sorted by date and start time.

### Per-event schema

| key | type | description |
|---|---|---|
| `name` | `str` | event `SUMMARY` |
| `date` | `datetime.date` | start date (in Madrid) |
| `start` | `datetime.time` | start time (in Madrid) |
| `end` | `datetime.datetime` | end date and time (in Madrid) |
| `duration_hours` | `float` | `(end - start)` in hours |

`end` is returned as a full `datetime` so that events ending after midnight are
not lost (e.g. `Evento test 3`). `start` stays a `time` because its date is
already in `date`.

## Function logic

1. Open the file and parse it with `icalendar.Calendar.from_ical(...)`.
2. Walk the `VEVENT` components.
3. Extract `SUMMARY`, `DTSTART` and `DTEND` from each event.
4. Convert `DTSTART`/`DTEND` to `Europe/Madrid` with `.astimezone(MADRID)`.
5. Filter: include only if `date_from <= start.date() <= date_to`
   (inclusive range, from 00:00 of the first day to 23:59 of the last day).
   Filtering is based on the start date, not on overlap.
6. Compute `duration_hours = (end - start).total_seconds() / 3600`.
7. Sort by `(date, start)`.
8. Return the list of `dict`.

## Edge cases: how they are handled

- **Missing `DTEND` (and no `DURATION`):** `end = start` is assumed, i.e. a
  `0.0` duration. A `warnings.warn(...)` notice is emitted. Execution is not
  interrupted.
- **`DURATION` instead of `DTEND`:** `icalendar` already exposes it; when
  present, it is resolved with `start + duration` to get `end`.
- **Missing `SUMMARY`:** an empty string `""` is used as the name.
- **Events without a time (all-day):** out of scope by explicit decision; not
  handled.
- **Recurrences (`RRULE`):** out of scope; only the first occurrence found in
  the `VEVENT` is read.
- **Timezones:** converted to `Europe/Madrid` (see "Settled decisions").

## Implementation steps

Done:

1. **Rename** package and project; remove `[project.scripts]`; `uv lock`.
2. **Add dependency:** `uv add icalendar`.
3. **Implement `read_events`** in `src/calendar_reader/__init__.py`.
4. **Test data:** move the `.ics` to `tests/fixtures/test_calendar.ics`.
5. **Manual script:** create `scripts/try_calendar.py`, which calls
   `read_events` on the fixture `.ics` and prints it.
6. **Documentation:** `README.md` with the signature, usage example and
   limitations.

Pending:

7. **Run the script** against the real `.ics` to validate the output.
   `uv run python scripts/try_calendar.py`

## Out of scope

- CLI and console entry point.
- Expanding recurrences (`RRULE`).
- All-day events.
- Automated tests (to be added with `pytest` when needed).
- Export to Excel/JSON and the future web app.

## Known risks

- If a floating event (no timezone) ever appeared, `.astimezone(MADRID)` would
  interpret it as system time; it is not expected in this calendar.
- The code is validated only with the manual script, not with automated tests.
