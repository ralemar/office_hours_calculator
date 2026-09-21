import io
import re
import unicodedata
import warnings
import zipfile
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar

MADRID = ZoneInfo("Europe/Madrid")

IGNORED_NAMES = {"cet opens", "cet closes"}
UNAVAILABLE_PATTERN = re.compile(r"\b(mimo|pryc)\b")


def _is_unavailable(name: str) -> bool:
    folded = name.casefold()
    if folded in IGNORED_NAMES:
        return True
    ascii_name = unicodedata.normalize("NFKD", folded).encode("ascii", "ignore").decode()
    return UNAVAILABLE_PATTERN.search(ascii_name) is not None


def read_events(source: str | Path | bytes, date_from: date, date_to: date) -> list[dict]:
    content = source if isinstance(source, bytes) else Path(source).read_bytes()
    if zipfile.is_zipfile(io.BytesIO(content)):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            entry = next((n for n in names if n.lower().endswith(".ics")), names[0])
            content = archive.read(entry)
    calendar = Calendar.from_ical(content)

    events = []
    for component in calendar.walk("VEVENT"):
        dtstart = component["DTSTART"].dt
        if not isinstance(dtstart, datetime):
            continue

        name = str(component.get("SUMMARY", "")).strip()
        if _is_unavailable(name):
            continue

        start = dtstart.astimezone(MADRID)
        if start.date() < date_from or start.date() > date_to:
            continue

        if "DTEND" in component:
            end = component["DTEND"].dt.astimezone(MADRID)
        elif "DURATION" in component:
            end = start + component["DURATION"].dt
        else:
            warnings.warn(f"Event '{name}' has no DTEND or DURATION; assuming zero duration")
            end = start

        events.append(
            {
                "name": name,
                "date": start.date(),
                "start": start.time(),
                "end": end,
                "duration_hours": (end - start).total_seconds() / 3600,
            }
        )

    events.sort(key=lambda event: (event["date"], event["start"]))
    return events
