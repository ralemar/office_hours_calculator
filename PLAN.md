# PLAN: Filter unavailable-worker events (all-day, "mimo" / "pryč")

## Goal

Some events mark that a worker is not available those days. They are usually
all-day events and their name contains `mimo` or `pryč`. They must be excluded
from the analysis (both the events table and the hours-per-person totals).

## Important finding first

Today the code assumes every event has a time:

```python
start = component["DTSTART"].dt.astimezone(MADRID)
```

For an all-day event, `DTSTART` is a `datetime.date` (no time), and `date` has no
`.astimezone`, so the function would **crash** with `AttributeError`. So handling
all-day events is not optional anymore.

## Idea A - Filter by name (recommended)

Extend the current ignore logic from exact names to substrings. Keep the existing
`IGNORED_NAMES` for exact matches (`CET opens`, `CET closes`) and add a keyword
list for partial matches:

```python
UNAVAILABLE_KEYWORDS = ("mimo", "pryč")

...
name = str(component.get("SUMMARY", "")).strip()
folded = name.casefold()
if folded in IGNORED_NAMES or any(k in folded for k in UNAVAILABLE_KEYWORDS):
    continue
```

- Case-insensitive via `casefold()`.
- Substring match, so `Pryč - dovolená` or `Mimo kancelář` are caught too.
- This check must run **before** touching `DTSTART`, so the all-day crash never
  happens for these events.

### Diacritics caveat

`casefold()` handles case but not accents: `pryč` != `pryc`. If a calendar ever
writes the keyword without the diacritic, normalize first, e.g. with
`unicodedata.normalize("NFKD", name)` and dropping combining marks, or add both
spellings (`"pryč"`, `"pryc"`) to the keyword list. Simplest for now: list both
spellings.

## Idea B - Filter all-day events structurally

Independent of the name, treat any all-day event (DTSTART is a `date`, not a
`datetime`) as "not a shift". Options:

1. **Skip it** entirely (cleanest for a work-hours analysis, since a day-long
   event has no meaningful hour count).
2. Keep it but with `0` hours / no times (adds complexity for little value).

Recommended: skip all-day events. This also protects against any all-day event
that does not match the keywords.

## Idea C - Use calendar flags instead of the name

All-day "out of office" events sometimes carry `TRANSP:TRANSPARENT`,
`STATUS:TENTATIVE` or `X-MICROSOFT-CDO-BUSYSTATUS:FREE`. Matching those would be
more "semantic", but they are not guaranteed and vary by provider, so the name
keywords are the most reliable signal here. Could be layered later.

## Recommended combination

- **A + B**: check the name keywords first, then skip any remaining all-day
  event. Covers the described events and avoids the crash for any other all-day
  event.

Proposed order inside the `VEVENT` loop:

1. Read and normalize `name`.
2. Skip if it matches `IGNORED_NAMES` or `UNAVAILABLE_KEYWORDS`.
3. Skip if `DTSTART` is a `date` without time (all-day).
4. Continue with the existing time-based logic.

## Edge cases

- `pryč` with or without diacritics: handled by listing both, or normalizing.
- Keyword as part of another word (e.g. a name containing "mimo"): substring
  match could over-filter; switch to word boundaries with `re` if it happens.
- All-day event with `DTEND` but no time: skipped in step 3, so duration is never
  computed.
- Multi-day unavailability: same, skipped as an all-day event.
- Does not affect the `CET opens` / `CET closes` handling, zip support or
  timezone conversion.

## Open questions

- Skip all-day events always (B.1), or only when they match the keywords?
- Is substring matching acceptable, or should it be whole-word?
- Should the keywords be a configurable parameter later (like the manual
  removal idea)?
