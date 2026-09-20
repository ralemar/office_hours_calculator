# PLAN: ICS calendar reader + Streamlit web app

## Goal

A small tool that reads an ICS calendar and, given two limit dates, returns the
events within that range with:

- Event name
- Date
- Start time
- End time
- Duration (in hours)

It has two consumers:

1. A reusable Python function (`read_events`) for scripts and tests.
2. A simple Streamlit web app where the user uploads the `.ics` and picks the
   date limits.

There is **no CLI**.

## Settled decisions

- **ICS library:** `icalendar`, the only library dependency besides Streamlit.
- **Web app:** Streamlit, as a thin UI layer on top of the package. No UI code
  inside `src/calendar_reader/`.
- **Minimal code:** an event is a flat `dict`.
- **Timezones:** the real `.ics` stores times in UTC (`Z`), even though the
  calendar is from Madrid. Times are converted to **`Europe/Madrid`** with
  `ZoneInfo("Europe/Madrid")` before filtering and displaying. On Windows,
  `tzdata` comes in with `icalendar`.
- **No automated tests at this stage:** validation is manual.
- **All files, code and docs in English.**

## Final structure

```
.
├── .streamlit/
│   └── config.toml            # optional, MUST stay at the repo root
├── app/
│   └── streamlit_app.py       # Streamlit entry point (Main file path on Cloud)
├── src/
│   └── calendar_reader/
│       └── __init__.py        # read_events()
├── tests/
│   └── fixtures/
│       └── test_calendar.ics  # real test calendar
├── scripts/
│   └── try_calendar.py        # local manual dump script
├── pyproject.toml
├── uv.lock
└── .python-version
```

- The Streamlit entry point lives in a subdirectory (`app/`). Community Cloud
  runs `streamlit run` from the repo root and the main file is set in the
  deployment panel, so a subdirectory is fine.
- The only `.streamlit/config.toml` recognized by Cloud is the one at the repo
  root; it is not read from `app/`.

## Public API

`src/calendar_reader/__init__.py`

```python
def read_events(source: str | Path | bytes, date_from, date_to) -> list[dict]:
    ...
```

- `source`: path to the `.ics`, or its raw `bytes` (what Streamlit's uploader
  provides via `.getvalue()`).
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

`end` is a full `datetime` so events ending after midnight are not lost.
`start` stays a `time` because its date is already in `date`.

## Function logic

1. Read the source: if `bytes`, use them directly; otherwise `Path(source).read_bytes()`.
2. Parse with `icalendar.Calendar.from_ical(...)`.
3. Walk the `VEVENT` components.
4. Extract `SUMMARY`, `DTSTART`, `DTEND`.
5. Convert `DTSTART`/`DTEND` to `Europe/Madrid` with `.astimezone(MADRID)`.
6. Filter: include only if `date_from <= start.date() <= date_to` (inclusive).
7. Compute `duration_hours = (end - start).total_seconds() / 3600`.
8. Sort by `(date, start)` and return.

## Web app

`app/streamlit_app.py`:

- `st.file_uploader("Upload your .ics calendar", type=["ics"])`.
- Two `st.date_input` fields for `date_from` / `date_to`, validated
  (`date_from <= date_to`).
- A button that calls `read_events(uploaded.getvalue(), date_from, date_to)`.
- Show the result with `st.dataframe`; a friendly message when there are none.
- `st.set_page_config` for the title/icon.

Run locally from the repo root:

```powershell
uv run streamlit run app/streamlit_app.py
```

## Edge cases

- **Missing `DTEND` (and no `DURATION`):** `end = start` (0 h) and a
  `warnings.warn(...)` notice.
- **`DURATION` instead of `DTEND`:** resolved as `start + duration`.
- **Missing `SUMMARY`:** empty string.
- **All-day events / recurrences:** out of scope by explicit decision.
- **Timezones:** converted to `Europe/Madrid`.

## Deployment notes (Streamlit Community Cloud)

- Main file path: `app/streamlit_app.py` (set in the deployment panel).
- Dependency file: Cloud searches the entry point's directory first, then the
  repo root, with priority `uv.lock` > `Pipfile` > `environment.yml` >
  `requirements.txt` > `pyproject.toml`. The root `uv.lock` is used, and
  `uv sync` installs the local `calendar_reader` package (it has a
  `build-system`), so the import works in the cloud.
- Do **not** add a `requirements.txt` inside `app/`; it would take precedence
  over `uv.lock`.
- Working directory on Cloud is the repo root; run locally from the root too.
- Config file must be at `.streamlit/config.toml` in the repo root.
- Python: Cloud only allows stable versions with security support. `3.14` is
  stable; if it is ever unavailable, lower `requires-python` and
  `.python-version`.
- Secrets, if ever needed, go in `.streamlit/secrets.toml` (never committed).

## Implementation steps

1. `uv add streamlit`.
2. Refactor `read_events` to accept `bytes | str | Path`.
3. Create `app/streamlit_app.py`.
4. Add `.streamlit/config.toml`.
5. Update `README.md` (usage, run command, deployment).
6. Verify locally: `scripts/try_calendar.py` and a Streamlit boot check.

## Out of scope

- CLI and console entry point.
- Expanding recurrences (`RRULE`).
- All-day events.
- Automated tests.
- Export to Excel/JSON.
