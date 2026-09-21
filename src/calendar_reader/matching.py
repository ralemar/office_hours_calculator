import warnings

from typesafe_sdk import Choice, TypeSafeClient

OTHER = "other"
UNDETERMINED = "UNDETERMINED"
MIN_CONFIDENCE = 0.6
MIN_MARGIN = 0.15

MATCH_QUESTION = "Which worker does `event_name` represent?"

GUIDELINES = (
    "The event name may be lowercase, include a duration in parentheses, or use "
    "only the surname initial. Choose 'other' if it does not clearly refer to one "
    "worker. If several options share the same first name but one is an exact "
    "match, choose that one."
)


def match_workers(
    names: list[str],
    workers: list[str],
    api_key: str,
    min_confidence: float = MIN_CONFIDENCE,
    min_margin: float = MIN_MARGIN,
) -> dict[str, str]:
    if not names or not workers:
        return {name: UNDETERMINED for name in names}

    criteria = {worker: worker for worker in workers}
    criteria[OTHER] = "Does not clearly match any worker (unclear, ambiguous, or not a worker)"

    questions = {
        f"event_{i}": Choice(
            instructions={"event_name": name, "question": MATCH_QUESTION},
            criteria=criteria,
        )
        for i, name in enumerate(names)
    }
    state = {"workers": list(workers), "guidelines": GUIDELINES}

    with TypeSafeClient(api_key=api_key) as client:
        response = client.system_one(state=state, questions=questions)

    return {
        name: _pick(response.answers[f"event_{i}"], min_confidence, min_margin)
        for i, name in enumerate(names)
    }


def _pick(answer, min_confidence, min_margin):
    if answer.choice == OTHER or answer.confidence < min_confidence:
        return UNDETERMINED
    top = sorted(answer.probabilities.values(), reverse=True)
    if len(top) >= 2 and top[0] - top[1] < min_margin:
        return UNDETERMINED
    return answer.choice


def assign_workers(
    events: list[dict],
    workers: list[str],
    api_key: str,
    min_confidence: float = MIN_CONFIDENCE,
    min_margin: float = MIN_MARGIN,
) -> list[dict]:
    try:
        mapping = match_workers(
            [event["name"] for event in events],
            workers,
            api_key,
            min_confidence,
            min_margin,
        )
    except Exception as error:
        warnings.warn(f"Worker matching failed, no event was matched: {error}")
        mapping = {}

    assigned = []
    for event in events:
        item = dict(event)
        item["worker"] = mapping.get(event["name"], UNDETERMINED)
        assigned.append(item)
    return assigned
