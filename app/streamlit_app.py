from datetime import date, timedelta

import streamlit as st

from calendar_reader import read_events

st.set_page_config(page_title="ICS Calendar Reader")

st.title("ICS Calendar Reader")
st.write("Upload an .ics calendar and pick a date range to list its events.")

uploaded = st.file_uploader("Upload your .ics calendar", type=["ics"])

today = date.today()
col_from, col_to = st.columns(2)
with col_from:
    date_from = st.date_input("From", value=today)
with col_to:
    date_to = st.date_input("To", value=today + timedelta(days=30))

if st.button("Scan events"):
    if uploaded is None:
        st.warning("Please upload an .ics file first.")
    elif date_from > date_to:
        st.error("The 'From' date must be before or equal to the 'To' date.")
    else:
        events = read_events(uploaded.getvalue(), date_from, date_to)
        if events:
            st.dataframe(events)
        else:
            st.info("No events found in that date range.")
