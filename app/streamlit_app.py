from datetime import date, timedelta

import streamlit as st

from calendar_reader.reader import read_events
from calendar_reader.analytics import total_hours_by_person
from calendar_reader.matching import UNDETERMINED, assign_workers
from calendar_reader.workers import parse_workers

st.set_page_config(page_title="ICS Calendar Reader")

st.title("ICS Calendar Reader")
st.write("Upload an .ics or .zip calendar, a workers list, and pick a date range.")

uploaded = st.file_uploader("Upload your .ics or .zip calendar", type=["ics", "zip"])

workers_file = st.file_uploader("Workers list (.txt, one name per line)", type=["txt"])
workers = parse_workers(workers_file.getvalue().decode("utf-8")) if workers_file else []
if workers:
    st.caption(f"{len(workers)} workers loaded")

today = date.today()
col_from, col_to = st.columns(2)
with col_from:
    date_from = st.date_input("From", value=today)
with col_to:
    date_to = st.date_input("To", value=today + timedelta(days=30))

if st.button("Scan events"):
    try:
        api_key = st.secrets["TYPESAFE_API_KEY"]
    except KeyError:
        api_key = None
        st.error("Missing TYPESAFE_API_KEY in Streamlit secrets.")

    if uploaded is None:
        st.warning("Please upload an .ics or .zip file first.")
    elif not workers:
        st.warning("Please upload a workers list first.")
    elif api_key is None:
        pass
    elif date_from > date_to:
        st.error("The 'From' date must be before or equal to the 'To' date.")
    else:
        events = read_events(uploaded.getvalue(), date_from, date_to)
        if events:
            assigned = assign_workers(events, workers, api_key)
            st.subheader("Events")
            st.dataframe(assigned)
            st.subheader("Hours per worker")
            st.dataframe(total_hours_by_person(assigned))
            undetermined = [e["name"] for e in assigned if e["worker"] == UNDETERMINED]
            if undetermined:
                st.warning("Could not determine: " + ", ".join(undetermined))
        else:
            st.info("No events found in that date range.")
