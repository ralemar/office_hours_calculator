import sys
from datetime import date
from pathlib import Path

from calendar_reader import read_events, total_hours_by_person

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "test_calendar.ics"
path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH

events = read_events(path, date(2026, 9, 1), date(2026, 10, 31))

print("Events")
for event in events:
    print(f"{event['date']} {event['start']}-{event['end'].time()} ({event['duration_hours']}h) {event['name']}")

print("\nHours per person")
for row in total_hours_by_person(events):
    print(f"{row['total_hours']}h {row['name']}")
