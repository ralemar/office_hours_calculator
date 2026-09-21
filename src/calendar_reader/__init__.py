import io
import warnings
import zipfile
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar

MADRID = ZoneInfo("Europe/Madrid")


def read_events(source: str | Path | bytes, date_from: date, date_to: date) -> list[dict]:
    content = source if isinstance(source, bytes) else Path(source).read_bytes()
    if zipfile.is_zipfile(io.BytesIO(content)):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            name = next((n for n in names if n.lower().endswith(".ics")), names[0])
            content = archive.read(name)
    calendar = Calendar.from_ical(content)

    events = []
    for component in calendar.walk("VEVENT"):
        start = component["DTSTART"].dt.astimezone(MADRID)
        if start.date() < date_from or start.date() > date_to:
            continue

        if "DTEND" in component:
            end = component["DTEND"].dt.astimezone(MADRID)
        elif "DURATION" in component:
            end = start + component["DURATION"].dt
        else:
            warnings.warn(f"Event '{component.get('SUMMARY', '')}' has no DTEND or DURATION; assuming zero duration")
            end = start

        events.append(
            {
                "name": str(component.get("SUMMARY", "")),
                "date": start.date(),
                "start": start.time(),
                "end": end,
                "duration_hours": (end - start).total_seconds() / 3600,
            }
        )

    events.sort(key=lambda event: (event["date"], event["start"]))
    return events
