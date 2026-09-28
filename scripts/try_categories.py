from datetime import date
from pathlib import Path

import streamlit as st

from calendar_reader.reader import read_events
from calendar_reader.categories import categorize

ICS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "test_categories.ics"

events = read_events(ICS, date(2026, 9, 1), date(2026, 10, 31))
categorized = categorize(events, st.secrets["TYPESAFE_API_KEY"])

print("name -> category")
for event in categorized:
    print(f"  {event['name']} -> {event['category']}")
