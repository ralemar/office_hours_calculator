from .matching import UNDETERMINED


def total_hours_by_person(events: list[dict]) -> list[dict]:
    totals: dict[str, float] = {}
    for event in events:
        worker = event.get("worker", event["name"])
        if worker == UNDETERMINED:
            continue
        totals[worker] = totals.get(worker, 0.0) + event["duration_hours"]

    summary = [{"name": name, "total_hours": round(hours, 2)} for name, hours in totals.items()]
    summary.sort(key=lambda row: row["name"].casefold())
    return summary
