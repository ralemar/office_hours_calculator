# calendar-reader

Reads the events of an ICS calendar that fall within a date range.

## Usage

```python
from datetime import date
from calendar_reader.reader import read_events

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

Events whose name contains the standalone word `mimo` or `pryč` (any diacritics,
e.g. `pryc`/`pryč`; surrounded only by non-letters such as spaces or parentheses)
are skipped. All-day events are always skipped. Everything else (including
`CET opens`/`CET closes`, `Czechtivity` and `Cz exams`) is returned and later
categorized by Jev.

## Categorizing events (Jev)

`categorize(events, api_key)` labels every event with one `category`:

- `Opening/Closing`: daily `CET opens` / `CET closes` markers.
- `Exams`: `Cz exams` events.
- `Czechtivity`: `Czechtivity` activities.
- `Office hours`: a worker's office hours (the ones to analyze).
- `Undetermined`: anything else.

```python
from calendar_reader.categories import categorize

events = categorize(events, st.secrets["TYPESAFE_API_KEY"])
```

Only `Office hours` events are summed; the rest are still shown in the app so the
user can fix a wrong category. On API failure every event becomes `Undetermined`.

## Hours per person

When event names identify a person (each event is a work shift),
`total_hours_by_person(events)` sums the durations of the events sharing the
same name:

```python
from calendar_reader.reader import read_events
from calendar_reader.analytics import total_hours_by_person

events = read_events("agenda.ics", date(2026, 9, 1), date(2026, 9, 30))

for row in total_hours_by_person(events):
    print(row["name"], row["total_hours"])
```

It returns a list of `dict` with keys `name` (`str`) and `total_hours` (`float`,
rounded to 2 decimals), sorted alphabetically by worker name.

## Matching event names to a worker list (Jev)

Event names rarely match a worker list exactly (lowercase, durations in
parentheses, surname initials). Pass the worker list and the API key to let the
official `typesafe-sdk` map each name to a worker:

```python
from datetime import date
import streamlit as st
from calendar_reader.reader import read_events
from calendar_reader.analytics import total_hours_by_person
from calendar_reader.matching import assign_workers

events = read_events("agenda.ics", date(2026, 9, 1), date(2026, 9, 30))
workers = ["Šimon", "Aneta Š", "Aneta Nováková"]

assigned = assign_workers(events, workers, st.secrets["TYPESAFE_API_KEY"])

for event in assigned:
    print(event["name"], "->", event["worker"])  # "UNDETERMINED" if ambiguous

# Aggregate the already-assigned events
for row in total_hours_by_person(assigned):
    print(row["name"], row["total_hours"])
```

- `assign_workers(events, workers, api_key)` only assigns: it creates a
  `TypeSafeClient` internally and adds a `worker` key per event.
- A name gets `worker = "UNDETERMINED"` when Jev chooses `other`, the
  `confidence` is below `0.6`, or the top probabilities are too close (ambiguous).
- `total_hours_by_person(events)` only sums: it groups by the `worker` key when
  present (falling back to `name`) and skips `UNDETERMINED`. Assign first, sum
  after; the two steps are independent.
- `matching.py` has no Streamlit dependency. Whoever reads the key (the app or a
  script, e.g. from `st.secrets`) passes it in. If the API fails, events are left
  unmatched and a warning is emitted.

## Inferring the duration from the event text (Jev)

Sometimes the event text (the `DESCRIPTION`, falling back to the name) states the
hours to register even when the start/end times do not match. `assign_durations`
asks Jev two Choice questions per event: whole **hours** (0-12) and **minutes**
(0-60 in steps of 5), and adds `inferred_hours` and `inferred_minutes` to each
event:

```python
from calendar_reader.durations import assign_durations

assigned = assign_durations(assigned, st.secrets["TYPESAFE_API_KEY"])
for event in assigned:
    print(event["name"], event["inferred_hours"], "h", event["inferred_minutes"], "m")
```

If the API fails, it warns and every event gets `0`/`0`.

## Web app

A small Streamlit app lets you upload an `.ics` or `.zip` calendar and a
`workers.txt` list (one name per line), pick the date range, and see the events
matched to each worker plus the total hours per worker. The grid shows the event
`Date` (leftmost, and the grid is ordered by it), `name`, the `category` (editable
dropdown), the `worker` (editable dropdown, preselected with the inferred worker)
and a single `Duration` (the Jev-inferred duration from the title by default,
formatted `3h 25m`). Only `Office hours`
events are summed; the others stay visible so a wrong category or worker can be
fixed. The grid is
[`streamlit-aggrid`](https://github.com/PablocFonseca/streamlit-aggrid): rows are
tinted by category (light yellow `Opening/Closing`, light gray `Exams`, light
orange `Czechtivity`, light purple `Undetermined`, white `Office hours`) across
all columns, and the color updates live when you change the category from its
dropdown. When the title duration differs from the event length, the `Duration`
cell shows a danger emoji (`⚠️`) and a **Duration conflicts** section appears where
you pick which one to use (default: from the title). A **Show only Office hours**
toggle lets you review the categories first and then hide the rest to focus on
workers and durations; category/worker edits are kept when toggling. The output
has two parts: **Hours per worker** (the per-worker summary table, to *see* the
result) and **Copy to Excel** (a transposed table with two rows, worker names
then total hours, ordered as in the `workers.txt` file, plus a **tab-separated
block with a copy button** to paste straight into Excel and a **CSV download**).
It reads the API key from `st.secrets["TYPESAFE_API_KEY"]`. Run it from the
repository root:

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
| `test_cet_filter.ics` | `CET opens`/`CET closes` markers (now categorized, not skipped) |
| `test_workers.ics` | worker-like names (`Šimon`, `Aneta Š`, ambiguous `Aneta`, unknown `Karel`) for Jev matching |
| `workers.txt` | reference worker list for `test_workers.ics` (one name per line) |
| `test_durations.ics` | duration texts with minutes (`3h 30m`, `45 min`, `1.5h`, `90 min`, `2:45`, `0h 25m`, no duration) for Jev duration inference |
| `workers_durations.txt` | reference worker list for `test_durations.ics` (one name per line) |
| `test_categories.ics` | one event of each Jev category; the `Czechtivity` events also carry a worker name (`... - Alice`, `... - Simon`) to check they are not mistaken for `Office hours` |

`scripts/try_workers.py` exercises the Jev matching with an invented worker list.
`scripts/try_durations.py` exercises the duration inference.
`scripts/try_categories.py` exercises the categorization. The API key is read
with Streamlit's native `st.secrets` (`TYPESAFE_API_KEY`):

```powershell
uv run python scripts/try_workers.py
uv run python scripts/try_durations.py
uv run python scripts/try_categories.py
```

## Limitations

- Does not expand recurring events (`RRULE`).
- All-day events are skipped (they have no meaningful hour count).
- Times are converted to `Europe/Madrid`; on Windows this requires `tzdata`
  (already pulled in as a dependency of `icalendar`).
- If an event has no `DTEND` or `DURATION`, a zero duration is assumed and a
  `warnings.warn` notice is emitted.
- For `.zip` input, it assumes the archive holds the calendar (a single `.ics` is
  used).
- Worker matching sends the event names to the TypeSafe AI cloud and needs an API
  key, so it does not work offline.
