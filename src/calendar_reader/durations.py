import warnings

from typesafe_sdk import Choice, TypeSafeClient

HOUR_OPTIONS = [str(hour) for hour in range(13)]
MINUTE_OPTIONS = [str(minute) for minute in range(0, 61, 5)]

DURATION_GUIDELINES = (
    "The event text may describe a duration, for example '8h', '3h 30m', "
    "'5 hodin', '(3h)' or '2:45' (hours:minutes). For the hours question return "
    "only the whole hours. For the minutes question return only the minutes, "
    "rounded to the nearest 5. If the text does not describe a duration, return 0 "
    "for both."
)


def infer_durations(texts: list[str], api_key: str) -> list[tuple[int, int]]:
    if not texts:
        return []

    questions = {}
    for i, text in enumerate(texts):
        questions[f"hours_{i}"] = Choice(
            instructions={
                "event_text": text,
                "question": "How many whole hours does the duration in `event_text` describe? Do not count the minutes.",
            },
            criteria={option: option for option in HOUR_OPTIONS},
        )
        questions[f"minutes_{i}"] = Choice(
            instructions={
                "event_text": text,
                "question": "How many minutes does the duration in `event_text` describe? Do not count the hours.",
            },
            criteria={option: option for option in MINUTE_OPTIONS},
        )

    state = {"guidelines": DURATION_GUIDELINES}
    with TypeSafeClient(api_key=api_key) as client:
        response = client.system_one(state=state, questions=questions)

    return [
        (
            int(response.answers[f"hours_{i}"].choice),
            int(response.answers[f"minutes_{i}"].choice),
        )
        for i in range(len(texts))
    ]


def assign_durations(events: list[dict], api_key: str) -> list[dict]:
    texts = [event.get("description") or event["name"] for event in events]
    try:
        inferred = infer_durations(texts, api_key)
    except Exception as error:
        warnings.warn(f"Duration inference failed, no duration was inferred: {error}")
        inferred = [(0, 0)] * len(events)

    assigned = []
    for event, (hours, minutes) in zip(events, inferred):
        item = dict(event)
        item["inferred_hours"] = hours
        item["inferred_minutes"] = minutes
        assigned.append(item)
    return assigned
