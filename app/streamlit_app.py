from datetime import date, timedelta

import streamlit as st

from calendar_reader.reader import read_events
from calendar_reader.analytics import total_hours_by_person
from calendar_reader.categories import CATEGORIES, OFFICE, categorize
from calendar_reader.categories import UNDETERMINED as CATEGORY_UNDETERMINED
from calendar_reader.durations import assign_durations
from calendar_reader.matching import UNDETERMINED, assign_workers
from calendar_reader.workers import parse_workers


def format_minutes(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


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
        categorized = categorize(events, api_key)
        assigned = assign_workers(categorized, workers, api_key)
        st.session_state["assigned"] = assign_durations(assigned, api_key)
        st.session_state["scan_id"] = st.session_state.get("scan_id", 0) + 1

assigned = st.session_state.get("assigned")
if not assigned:
    st.info("Scan a calendar to list its events.")
else:
    columns = ["name", "category", "worker", "Duration (From title)", "Duration (Event length)"]
    options = list(
        dict.fromkeys(workers + [row["worker"] for row in assigned if row["worker"] != UNDETERMINED])
    )
    if UNDETERMINED not in options:
        options.append(UNDETERMINED)

    display = [
        {
            "name": row["name"],
            "category": row["category"],
            "worker": row["worker"],
            "Duration (From title)": format_minutes(
                row["inferred_hours"] * 60 + row["inferred_minutes"]
            ),
            "Duration (Event length)": format_minutes(round(row["duration_hours"] * 60)),
        }
        for row in assigned
    ]

    edited = st.data_editor(
        display,
        hide_index=True,
        column_order=columns,
        column_config={
            "category": st.column_config.SelectboxColumn(
                "category",
                options=CATEGORIES,
                required=True,
            ),
            "worker": st.column_config.SelectboxColumn(
                "worker",
                options=options,
                required=True,
            ),
        },
        disabled=[name for name in columns if name not in ("category", "worker")],
        key=f"events_editor_{st.session_state.get('scan_id', 0)}",
    )
    edited_rows = edited.to_dict("records") if hasattr(edited, "to_dict") else edited
    rows = [
        {**original, "category": edited_row["category"], "worker": edited_row["worker"]}
        for original, edited_row in zip(assigned, edited_rows)
    ]

    office = [row for row in rows if row["category"] == OFFICE]
    st.subheader("Hours per worker")
    st.dataframe(total_hours_by_person(office))

    unknown_category = [row["name"] for row in rows if row["category"] == CATEGORY_UNDETERMINED]
    if unknown_category:
        st.warning("Undetermined category: " + ", ".join(unknown_category))
    unmatched = [row["name"] for row in office if row["worker"] == UNDETERMINED]
    if unmatched:
        st.warning("Could not determine worker: " + ", ".join(unmatched))
