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

## Web app

A small Streamlit app lets you upload an `.ics` or `.zip` file and pick the date
range. Run it from the repository root:

```powershell
uv run streamlit run app/streamlit_app.py
```

## Test script

There is a test calendar at `tests/fixtures/test_calendar.ics` and a manual
script to dump it:

```powershell
uv run python scripts/try_calendar.py
```

## Limitations

- Does not expand recurring events (`RRULE`).
- Does not handle all-day events.
- Times are converted to `Europe/Madrid`; on Windows this requires `tzdata`
  (already pulled in as a dependency of `icalendar`).
- If an event has no `DTEND` or `DURATION`, a zero duration is assumed and a
  `warnings.warn` notice is emitted.
- For `.zip` input, it assumes the archive holds the calendar (a single `.ics` is
  used).
