import io
import warnings
import zipfile
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar

MADRID = ZoneInfo("Europe/Madrid")

IGNORED_NAMES = {"cet opens", "cet closes"}


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
        name = str(component.get("SUMMARY", "")).strip()
        if name.casefold() in IGNORED_NAMES:
            continue

        start = component["DTSTART"].dt.astimezone(MADRID)
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


def total_hours_by_person(events: list[dict]) -> list[dict]:
    totals: dict[str, float] = {}
    for event in events:
        totals[event["name"]] = totals.get(event["name"], 0.0) + event["duration_hours"]

    summary = [{"name": name, "total_hours": round(hours, 2)} for name, hours in totals.items()]
    summary.sort(key=lambda row: row["total_hours"], reverse=True)
    return summary
