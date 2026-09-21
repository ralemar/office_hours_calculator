# PLAN: Ignore "CET opens" / "CET closes" events

## Goal

Some events in the calendar are named `CET opens` and `CET closes`. They are
markers, not real activities, so they must be excluded from the analysis.
Nothing else should change.

## Where to filter

Best place is inside `read_events` in `src/calendar_reader/__init__.py`, so both
the Streamlit app and `scripts/try_calendar.py` get the behavior for free. Doing
it in the UI would be lost as soon as the function is called from elsewhere.

## Approach (recommended)

Add a module-level constant with the names to skip and check it while walking
the events, before the event is appended:

```python
IGNORED_NAMES = {"cet opens", "cet closes"}


def read_events(source, date_from, date_to):
    ...
    for component in calendar.walk("VEVENT"):
        name = str(component.get("SUMMARY", "")).strip()
        if name.casefold() in IGNORED_NAMES:
            continue
        ...
```

- The constant stores names already normalized (lowercase) to compare against
  `name.casefold()`.
- `.strip()` removes accidental surrounding spaces.
- The check happens **before** the date filter/appending, so ignored events cost
  no extra work.

## Matching rule options

1. **Exact, case-insensitive, trimmed** (recommended): only `CET opens` and
   `CET closes` (any casing/spacing) are dropped. Lowest risk of dropping a real
   event by accident.
2. **Prefix `cet `**: also drops any future event starting with `CET ...`.
   Convenient, but could hide something you actually want.
3. **Substring**: too broad; not recommended.

## Optional: make it configurable

Instead of a fixed constant, add a parameter with a default:

```python
def read_events(source, date_from, date_to, ignore=IGNORED_NAMES):
    ...
```

This keeps current behavior by default and lets the future web app expose the
list if needed. Slightly more code; only worth it if configurability is wanted.

## Edge cases

- `CET opens` written with different case (`cet opens`, `Cet Opens`): handled by
  `casefold()`.
- Trailing/leading spaces in the `SUMMARY`: handled by `strip()`.
- Missing `SUMMARY`: the empty string is not in the set, so the event is kept.
- Does not affect zip handling, timezone conversion, duration or ordering.

## Verification

1. Add a temporary event named `CET opens` (or use a real `.ics` that has them)
   inside the chosen date range.
2. Run `uv run python scripts/try_calendar.py` and confirm the `CET opens` /
   `CET closes` entries are absent while the rest is unchanged.
3. Regression: the existing test calendar output must stay the same (it has no
   `CET` events).

## Decisions

- **Exact match (option 1)**: only `CET opens` / `CET closes`, compared
  case-insensitively and trimmed.
- **Fixed constant** for now. Manual removal or broader configuration may be
  added later.
