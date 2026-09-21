# PLAN: Accept zipped ICS uploads

## Goal

Allow the user to upload the Google Calendar export as-is: a `.zip` archive
containing the `.ics`. No need to unzip beforehand, and no new dependencies.

## Decision

Handle the zip detection inside `read_events` (not in the app), so both the
Streamlit app and the manual script get the behavior for free. Detection is by
content (`zipfile.is_zipfile`), not by file extension.

## Changes

1. **`src/calendar_reader/__init__.py`**
   - Add `import io` and `import zipfile` (standard library only).
   - After obtaining `content`, if it is a zip, open it and read the first entry
     ending in `.ics` (case-insensitive). If the archive has no `.ics`, fall back
     to the first entry.
   - No other logic changes: paths and raw `.ics` bytes keep working as before.

2. **`app/streamlit_app.py`**
   - `st.file_uploader(..., type=["ics", "zip"])`.
   - Updated labels/warnings to mention `.zip`.
   - No error handling added (invalid files still surface Streamlit's traceback).

3. **`README.md`**
   - Document that `source` accepts `.ics` bytes or a `.zip` containing it.
   - Mention it in the web app section and limitations.

## Verification

- Regression: `uv run python scripts/try_calendar.py` (path to `.ics`).
- Zip: generate a temporary `.zip` outside the repo with the test `.ics` inside
  and call `read_events` with its bytes; the output must match the regression.

## Out of scope

- Zip files with several `.ics` (only the first is used).
- Password-protected archives.
- Friendly error handling in the app.
