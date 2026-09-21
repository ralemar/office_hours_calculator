# calendar-reader

Reads the events of an ICS calendar that fall within a date range.

## Usage

```python
from datetime import date
from calendar_reader import read_events

events = read_events("agenda.ics", date(2026, 9, 1), date(2026, 9, 30))

for event in events:
    print(event["name"], event["date"], event["start"], event["end"], event["duration_hours"])
```

`read_events(source, date_from, date_to)` returns a list of `dict` sorted by date
and start time, with the following keys:

| key | type | description |
|---|---|---|
| `name` | `str` | event `SUMMARY` |
| `date` | `datetime.date` | start date |
| `start` | `datetime.time` | start time |
| `end` | `datetime.datetime` | end date and time (timezone-aware) |
| `duration_hours` | `float` | duration in hours |

`source` can be a path (`str`/`Path`) or the raw bytes of an `.ics` **or a
`.zip` containing it**. When a zip is given, the first `.ics` inside is used
(Google Calendar exports a compressed archive).

The range is inclusive: from 00:00 of `date_from` to 23:59 of `date_to`, and it
is filtered by the event's start date. Times are returned converted to
`Europe/Madrid`.

Events named `CET opens` or `CET closes` (case-insensitive, surrounding spaces
ignored) are skipped, as are events whose name contains the standalone word
`mimo` or `pryč` (any diacritics, e.g. `pryc`/`pryč`; surrounded only by
non-letters such as spaces or parentheses). All-day events are always skipped.

## Hours per person

When event names identify a person (each event is a work shift),
`total_hours_by_person(events)` sums the durations of the events sharing the
same name:

```python
from calendar_reader import read_events, total_hours_by_person

events = read_events("agenda.ics", date(2026, 9, 1), date(2026, 9, 30))

for row in total_hours_by_person(events):
    print(row["name"], row["total_hours"])
```

It returns a list of `dict` with keys `name` (`str`) and `total_hours` (`float`,
rounded to 2 decimals), sorted by total hours descending.

## Web app

A small Streamlit app lets you upload an `.ics` or `.zip` file and pick the date
range. Run it from the repository root:

```powershell
uv run streamlit run app/streamlit_app.py
```

## Test script and fixtures

`scripts/try_calendar.py` dumps the events and the hours per person for a
calendar. It defaults to `tests/fixtures/test_calendar.ics`, or takes a path:

```powershell
uv run python scripts/try_calendar.py
uv run python scripts/try_calendar.py tests/fixtures/test_hours.ics
```

Fixtures under `tests/fixtures/`:

| file | purpose |
|---|---|
| `test_calendar.ics` | real-world sample (UTC times, one event past midnight) |
| `test_calendar.zip` | a compressed calendar, to check `.zip` input |
| `test_hours.ics` | same person across days to check the totals (`Alice` 6.5 h, `Bob` 2 h) |
| `test_unavailable.ics` | all-day and `mimo`/`pryč` variants to check the filtering |
| `test_cet_filter.ics` | `CET opens`/`CET closes` markers to check they are skipped |

## Limitations

- Does not expand recurring events (`RRULE`).
- All-day events are skipped (they have no meaningful hour count).
- Times are converted to `Europe/Madrid`; on Windows this requires `tzdata`
  (already pulled in as a dependency of `icalendar`).
- If an event has no `DTEND` or `DURATION`, a zero duration is assumed and a
  `warnings.warn` notice is emitted.
- For `.zip` input, it assumes the archive holds the calendar (a single `.ics` is
  used).
