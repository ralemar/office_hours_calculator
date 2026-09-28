"""Generate a large test calendar (tests/fixtures/test_big.ics) and its worker list.

Reproducible: run `uv run python scripts/generate_test_big.py` to regenerate.
Around 100 events in September 2026, 3-4 per day, covering every case:
Office hours (some with a title/event-length conflict), CET opens/closes,
Czechtivity (with worker names), Cz exams, Undetermined, all-day and mimo.
"""

from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICAL = ROOT / "tests" / "fixtures" / "test_big.ics"
WORKERS_TXT = ROOT / "tests" / "fixtures" / "workers_big.txt"

WORKERS = [
    "Alice",
    "Bob",
    "Carol",
    "Dave",
    "Erin",
    "Frank",
    "Grace",
    "Heidi",
    "Ivan",
    "Judy",
    "Mallory",
    "Niaj",
    "Olivia",
    "Peggy",
    "Sybil",
    "Trent",
]

# (title duration text, event length in hours). The last two conflict with the title.
OFFICE = [
    ("8h", 8.0),
    ("3h 30m", 3.5),
    ("5h", 5.0),
    ("2h 15m", 2.25),
    ("6h 45m", 6.75),
    ("1h 30m", 1.5),
    ("4h", 5.0),
    ("7h", 6.0),
]


def utc(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%SZ")


def add_event(lines, summary, start, end, description=None, all_day=False):
    lines.append("BEGIN:VEVENT")
    lines.append(f"SUMMARY:{summary}")
    if description:
        lines.append(f"DESCRIPTION:{description}")
    if all_day:
        lines.append(f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{(start + timedelta(days=1)).strftime('%Y%m%d')}")
    else:
        lines.append(f"DTSTART:{utc(start)}")
        lines.append(f"DTEND:{utc(end)}")
    lines.append("END:VEVENT")


def main() -> None:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//calendar-reader//test//EN"]

    for day in range(1, 31):
        base = datetime(2026, 9, day, 7, 0, 0)

        add_event(lines, "CET opens", base, base + timedelta(minutes=30))
        add_event(lines, "CET closes", base + timedelta(hours=10), base + timedelta(hours=10, minutes=30))

        worker = WORKERS[day % len(WORKERS)]
        title, hours = OFFICE[day % len(OFFICE)]
        start = base + timedelta(hours=1)
        add_event(lines, f"{worker} ({title})", start, start + timedelta(hours=hours))

        if day % 2 == 0:
            worker2 = WORKERS[(day + 7) % len(WORKERS)]
            title2, hours2 = OFFICE[(day + 3) % len(OFFICE)]
            start2 = base + timedelta(hours=3)
            add_event(lines, f"{worker2} ({title2})", start2, start2 + timedelta(hours=hours2))

        if day % 5 == 0:
            worker3 = WORKERS[(day + 3) % len(WORKERS)]
            start3 = base + timedelta(hours=5)
            add_event(
                lines,
                f"Czechtivity - spring cleaning - {worker3}",
                start3,
                start3 + timedelta(hours=2),
                description=f"Czechtivity activity done by {worker3}",
            )
        if day % 7 == 0:
            start4 = base + timedelta(hours=6)
            add_event(lines, "Cz exams - level B2", start4, start4 + timedelta(hours=2, minutes=30))
        if day % 6 == 0:
            start5 = base + timedelta(hours=8)
            add_event(lines, "Team meeting", start5, start5 + timedelta(hours=1), description="Weekly sync")
        if day % 11 == 0:
            add_event(lines, "Mimo", base, base, all_day=True)
        if day % 13 == 0:
            worker4 = WORKERS[(day + 11) % len(WORKERS)]
            start6 = base + timedelta(hours=9)
            add_event(lines, f"Czechtivity - workshop - {worker4}", start6, start6 + timedelta(hours=1, minutes=30))

    lines.append("END:VCALENDAR")
    ICAL.write_text("\n".join(lines) + "\n", encoding="utf-8")
    WORKERS_TXT.write_text("\n".join(WORKERS) + "\n", encoding="utf-8")
    print(f"Wrote {ICAL} ({lines.count('BEGIN:VEVENT')} events)")
    print(f"Wrote {WORKERS_TXT} ({len(WORKERS)} workers)")


if __name__ == "__main__":
    main()
