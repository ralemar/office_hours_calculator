from datetime import date
from pathlib import Path

from calendar_reader import read_events

PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "test_calendar.ics"

for event in read_events(PATH, date(2026, 9, 1), date(2026, 10, 31)):
    print(f"{event['date']} {event['start']}-{event['end'].time()} ({event['duration_hours']}h) {event['name']}")
