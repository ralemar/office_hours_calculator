import warnings

from typesafe_sdk import Choice, TypeSafeClient

OPENING = "Opening/Closing"
EXAMS = "Exams"
CZECHTIVITY = "Czechtivity"
OFFICE = "Office hours"
UNDETERMINED = "Undetermined"

CATEGORIES = [OPENING, EXAMS, CZECHTIVITY, OFFICE, UNDETERMINED]

CATEGORY_QUESTION = "Which category does this event belong to?"

CATEGORY_GUIDELINES = (
    "Classify each event into exactly one category:\n"
    "- 'Opening/Closing': the daily 'CET opens' / 'CET closes' markers.\n"
    "- 'Exams': a 'Cz exams' event.\n"
    "- 'Czechtivity': a 'Czechtivity' activity (it has a description and the name "
    "of the worker doing it).\n"
    "- 'Office hours': a worker's recorded office hours; the text names a worker "
    "and usually a duration.\n"
    "- 'Undetermined': anything else."
)

CATEGORY_CRITERIA = {
    OPENING: "The daily 'CET opens' / 'CET closes' marker",
    EXAMS: "A 'Cz exams' event",
    CZECHTIVITY: "A 'Czechtivity' activity",
    OFFICE: "A worker's office hours (worker name, usually a duration)",
    UNDETERMINED: "None of the above",
}


def categorize(events: list[dict], api_key: str) -> list[dict]:
    if not events:
        return []

    questions = {
        f"event_{i}": Choice(
            instructions={
                "event_name": event["name"],
                "event_description": event.get("description", ""),
                "question": CATEGORY_QUESTION,
            },
            criteria=CATEGORY_CRITERIA,
        )
        for i, event in enumerate(events)
    }
    state = {"guidelines": CATEGORY_GUIDELINES}

    try:
        with TypeSafeClient(api_key=api_key) as client:
            response = client.system_one(state=state, questions=questions)
        categories = [response.answers[f"event_{i}"].choice for i in range(len(events))]
    except Exception as error:
        warnings.warn(f"Category inference failed, every event is UNDETERMINED: {error}")
        categories = [UNDETERMINED] * len(events)

    return [{**event, "category": category} for event, category in zip(events, categories)]
