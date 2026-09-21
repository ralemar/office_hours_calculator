# PLAN: Match event names to workers with the official Jev SDK

## Goal

Event names are worker identifiers, but they do not match the worker list
exactly: lowercase, durations in parentheses (`(Simon 8h)`, `Simon (5 hodin -
okna)`), or just the surname initial (`Jan N`). Match each event name to a
worker from a user-provided list and aggregate hours per worker, using Jev
(TypeSafe AI System One) through the **official** `typesafe-sdk`.

## Decisions

- Use the official SDK: `typesafe-sdk` (not `fuzzyif`).
- One single API request: several `Choice` questions, one per event name, in one
  `system_one(...)` call (no dedupe, no batches).
- If the API fails, unresolved names are excluded and reported; the app does not
  crash.
- Matching logic lives in a new `src/calendar_reader/matching.py`, separate from
  the ICS parsing.
- Ambiguity rule: mark as `"UNDETERMINED"` when `choice == "other"`,
  `confidence < 0.6`, or the top-2 probability margin is small.
- The worker list is a parameter for now; its UI is still to be decided.

## Dependency and configuration

- `uv add typesafe-sdk` (Python 3.10+; verify it installs on 3.14).
- API key: read by the caller (the app or a script) with Streamlit's `st.secrets`
  and passed to the matching functions. The package creates the client with
  `TypeSafeClient(api_key=api_key)`. Never commit the key.

## `src/calendar_reader/matching.py`

- `match_workers(names, workers, api_key, min_confidence=0.6, min_margin=0.15) -> dict[str, str]`:
  1. No dedupe and no batches: one `Choice` per event name in a single call (few
     names).
  2. `criteria = {worker: worker for worker in workers} + {"other": "does not
     clearly match any worker / ambiguous"}` (the worker is both the option name
     and the description, so the name is always sent).
  3. Instructions are just `"Which worker does \`event_name\` represent?"`. The
     shared answer guidelines (lowercase, duration in parentheses, surname
     initial, `other` when unclear, exact match wins) go in `state`, together
     with the worker list, since they are common to every question.
  4. Read `response.answers[f"event_{i}"]`; return `"UNDETERMINED"` if
     `choice == "other"`, `confidence < min_confidence`, or the top-2 margin is
     below `min_margin`.
- `assign_workers(events, workers, api_key, ...) -> list[dict]`: creates the client
  from the key and adds a `worker` key (canonical name or `"UNDETERMINED"`).
  Assignment only.

## Integration

- Two independent steps, each in its own module:
  1. `matching.assign_workers(events, workers, api_key, ...)` assigns a `worker`
     to each event (or `"UNDETERMINED"`).
  2. `analytics.total_hours_by_person(events)` sums by the `worker` key (falling
     back to `name` when absent) and skips `"UNDETERMINED"`.
- API failure is caught: affected names become `"UNDETERMINED"` and a warning is
  emitted.
- Unmatched/ambiguous names are listed separately for the warning
  (`[e["name"] for e in assigned if e["worker"] == "UNDETERMINED"]`).
- The web app is not wired yet: the worker list source and UX are pending.

## Limits and risks

- A `Choice` accepts at most 255 options; with more workers, chunk or go
  hierarchical.
- Latency is 70-500 ms per request; all names go in a single request.
- Privacy: worker names are sent to the TypeSafe cloud. This is a data-processing
  decision.
- External dependency + early access; the "exclude and warn" fallback keeps the
  app usable.

## Configuration and test data

- **API key**: the caller reads it with Streamlit's `st.secrets`
  (`st.secrets["TYPESAFE_API_KEY"]`) and passes it to `match_workers` /
  `assign_workers`. Global `~/.streamlit/secrets.toml` or project
  `.streamlit/secrets.toml` (git-ignored). Never commit it.
- **Worker list for tests**: pass a Python list to `match_workers` /
  `assign_workers`. For a file-based option, `tests/fixtures/workers.local.txt`
  (one name per line) added to `.gitignore`, since real names are personal data.

## Verification

- With a real key: `other`, low `confidence`, and small margin return
  `"UNDETERMINED"`; a clear case returns the canonical name.
- Cases: `(Simon 8h)`, `Simon (3h)`, `Aneta` vs `Aneta S`, and a name that
  matches no worker.
- Regression: `scripts/try_calendar.py` without `workers` must stay the same.

## Out of scope

- Worker-list UI and its persistence.
- Manual override mapping for ambiguous names.
- Automated tests.
