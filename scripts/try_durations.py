from datetime import date
from pathlib import Path

import streamlit as st

from calendar_reader.reader import read_events
from calendar_reader.durations import assign_durations

ICS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "test_durations.ics"

events = read_events(ICS, date(2026, 9, 1), date(2026, 10, 31))
assigned = assign_durations(events, st.secrets["TYPESAFE_API_KEY"])

print("name | description -> computed | inferred")
for event in assigned:
    print(
        f"  {event['name']} | {event['description']!r}"
        f" -> {event['duration_hours']}h"
        f" | {event['inferred_hours']}h {event['inferred_minutes']}m"
    )
