from datetime import date
from pathlib import Path

import streamlit as st

from calendar_reader.reader import read_events
from calendar_reader.analytics import total_hours_by_person
from calendar_reader.matching import UNDETERMINED, assign_workers

WORKERS = ["Šimon", "Aneta Š", "Aneta Nováková", "Jan Novák"]
ICS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "test_workers.ics"

events = read_events(ICS, date(2026, 9, 1), date(2026, 10, 31))

assigned = assign_workers(events, WORKERS, st.secrets["TYPESAFE_API_KEY"])

print("Events -> worker")
for event in assigned:
    print(f"  {event['name']} -> {event['worker']}")

print("\nHours per worker")
for row in total_hours_by_person(assigned):
    print(f"  {row['total_hours']}h {row['name']}")

unmatched = [event["name"] for event in assigned if event["worker"] == UNDETERMINED]
print("\nUnmatched:", unmatched)
