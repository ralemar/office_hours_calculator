import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, JsCode

from calendar_reader.reader import read_events
from calendar_reader.analytics import total_hours_by_person
from calendar_reader.categories import CATEGORIES, CZECHTIVITY, EXAMS, OFFICE, OPENING, categorize
from calendar_reader.categories import UNDETERMINED as CATEGORY_UNDETERMINED
from calendar_reader.durations import assign_durations
from calendar_reader.matching import UNDETERMINED, assign_workers
from calendar_reader.workers import parse_workers

CATEGORY_COLORS = {
    OPENING: "#FFF9C4",
    EXAMS: "#EEEEEE",
    CZECHTIVITY: "#FFE0B2",
    CATEGORY_UNDETERMINED: "#E1BEE7",
}

FROM_TITLE = "From title"
EVENT_LENGTH = "Event length"

ROW_STYLE = JsCode(
    "function(params) {"
    f"var colors = {json.dumps(CATEGORY_COLORS)};"
    "var color = colors[params.data.category];"
    "return color ? {background: color} : null;"
    "}"
)


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
    scan_id = st.session_state.get("scan_id", 0)
    current_key = f"current_{scan_id}"
    current = st.session_state.get(current_key, {})

    def current_category(index: int) -> str:
        return current.get(index, {}).get("category") or assigned[index]["category"]

    def current_worker(index: int) -> str:
        return current.get(index, {}).get("worker") or assigned[index]["worker"]

    inferred_minutes = [e["inferred_hours"] * 60 + e["inferred_minutes"] for e in assigned]
    event_minutes = [round(e["duration_hours"] * 60) for e in assigned]
    conflict = [inferred_minutes[i] != event_minutes[i] for i in range(len(assigned))]

    def choice_key(index: int) -> str:
        return f"duration_choice_{scan_id}_{index}"

    resolved_minutes = []
    for index in range(len(assigned)):
        if st.session_state.get(choice_key(index)) == EVENT_LENGTH:
            resolved_minutes.append(event_minutes[index])
        else:
            resolved_minutes.append(inferred_minutes[index])

    worker_options = list(
        dict.fromkeys(workers + [row["worker"] for row in assigned if row["worker"] != UNDETERMINED])
    )
    if UNDETERMINED not in worker_options:
        worker_options.append(UNDETERMINED)

    st.caption(
        "Step 1: check the category colors and fix them if needed. "
        "Step 2: toggle below to focus on Office hours (workers and durations)."
    )
    office_only = st.toggle(
        "Show only Office hours",
        key=f"office_only_{scan_id}",
    )

    order = sorted(range(len(assigned)), key=lambda i: (assigned[i]["date"], assigned[i]["start"]))
    indices = [index for index in order if not office_only or current_category(index) == OFFICE]

    if not indices:
        st.info("No Office hours events to show.")
    else:
        display = pd.DataFrame(
            [
                {
                    "_id": index,
                    "Date": assigned[index]["date"].isoformat(),
                    "name": assigned[index]["name"],
                    "category": current_category(index),
                    "worker": current_worker(index),
                    "Duration": format_minutes(resolved_minutes[index])
                    + (" ⚠️" if conflict[index] and current_category(index) == OFFICE else ""),
                }
                for index in indices
            ]
        )

        grid_builder = GridOptionsBuilder.from_dataframe(display)
        grid_builder.configure_column("_id", hide=True)
        grid_builder.configure_column("Date", editable=False, sort="asc")
        grid_builder.configure_column("name", editable=False)
        grid_builder.configure_column(
            "category",
            editable=True,
            cellEditor="agSelectCellEditor",
            cellEditorParams={"values": CATEGORIES},
        )
        grid_builder.configure_column(
            "worker",
            editable=True,
            cellEditor="agSelectCellEditor",
            cellEditorParams={"values": worker_options},
        )
        grid_builder.configure_column("Duration", editable=False)
        grid_options = grid_builder.build()
        grid_options["getRowStyle"] = ROW_STYLE

        response = AgGrid(
            display,
            gridOptions=grid_options,
            update_on=["cellValueChanged"],
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            allow_unsafe_jscode=True,
            theme="streamlit",
            height=min(600, 40 * len(display) + 45),
            key=f"events_grid_{scan_id}_{int(office_only)}",
        )

        for _, edited_row in response.data.iterrows():
            index = int(edited_row["_id"])
            entry = current.setdefault(index, {})
            category = edited_row["category"] if isinstance(edited_row["category"], str) else None
            worker = edited_row["worker"] if isinstance(edited_row["worker"], str) else None
            if category:
                entry["category"] = category
            if worker:
                entry["worker"] = worker
        st.session_state[current_key] = current

    rows = [
        {
            **original,
            "category": current_category(index),
            "worker": current_worker(index),
            "duration_hours": resolved_minutes[index] / 60,
        }
        for index, original in enumerate(assigned)
    ]

    conflicts = [index for index in order if current_category(index) == OFFICE and conflict[index]]
    if conflicts:
        with st.expander(f"Duration conflicts ({len(conflicts)})", expanded=True):
            st.caption(
                f"{len(conflicts)} office-hours event(s) where the title duration differs "
                "from the event length. Default: the duration from the title."
            )
            for index in conflicts:
                st.markdown(
                    f"**{assigned[index]['date'].isoformat()} — {assigned[index]['name']}** — "
                    f"{format_minutes(inferred_minutes[index])} vs {format_minutes(event_minutes[index])}"
                )

                def label(value, index=index):
                    minutes = inferred_minutes[index] if value == FROM_TITLE else event_minutes[index]
                    return f"{value} ({format_minutes(minutes)})"

                st.radio(
                    "Duration to use",
                    options=[FROM_TITLE, EVENT_LENGTH],
                    index=0 if st.session_state.get(choice_key(index)) != EVENT_LENGTH else 1,
                    format_func=label,
                    key=choice_key(index),
                    horizontal=True,
                    label_visibility="collapsed",
                )

    st.subheader("Hours per worker")
    office_rows = [row for row in rows if row["category"] == OFFICE]
    summary = total_hours_by_person(office_rows)
    st.dataframe(summary)

    st.subheader("Copy to Excel")
    totals_by_worker = {row["name"]: row["total_hours"] for row in summary}
    worker_names = list(workers)
    worker_hours = [totals_by_worker.get(name, 0.0) for name in worker_names]

    if not worker_names:
        st.info("No workers to show.")
    else:
        st.dataframe(pd.DataFrame([worker_hours], columns=worker_names), hide_index=True)

        separator = "\t"
        copy_values = separator.join(worker_names) + "\n" + separator.join(f"{hours:g}" for hours in worker_hours)
        st.caption("Copy the block and paste it into Excel (tab-separated, ordered as in the workers file).")
        st.code(copy_values, language="text")

        csv_values = ",".join(worker_names) + "\n" + ",".join(f"{hours:g}" for hours in worker_hours)
        st.download_button(
            "Download CSV",
            csv_values,
            file_name="worker_hours.csv",
            mime="text/csv",
        )

    unknown_category = [row["name"] for row in rows if row["category"] == CATEGORY_UNDETERMINED]
    if unknown_category:
        st.warning("Undetermined category: " + ", ".join(unknown_category))
    unmatched = [row["name"] for row in rows if row["category"] == OFFICE and row["worker"] == UNDETERMINED]
    if unmatched:
        st.warning("Could not determine worker: " + ", ".join(unmatched))
