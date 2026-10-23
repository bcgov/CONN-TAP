"""Pure helpers for CHEFS event-subscription callbacks (no web or HTTP deps).

CHEFS POSTs ``{formId, formVersion, subscriptionEvent, submissionId}`` to the
configured endpoint, with the configured Key/Endpoint token as a header. The
payload carries no answers; they are fetched separately with the form API key.
"""
from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Any

SUBMISSION_EVENT = "eventSubmission"

# Radio option *values* (not labels) from the CHEFS form -> document to send.
# Anything else, including "none", means no document.
DOCUMENT_BY_CHOICE = {
    "typeA": "A",
    "typeB": "B",
}


@dataclass(frozen=True)
class ChefsEvent:
    form_id: str
    subscription_event: str
    submission_id: str | None


def token_matches(expected: str, received: str | None) -> bool:
    if not expected or not received:
        return False
    return hmac.compare_digest(expected.encode(), received.encode())


def parse_event(payload: Any) -> ChefsEvent:
    if not isinstance(payload, dict):
        raise ValueError("Event body must be a JSON object")
    form_id = payload.get("formId")
    event = payload.get("subscriptionEvent")
    if not isinstance(form_id, str) or not isinstance(event, str):
        raise ValueError("Event body needs formId and subscriptionEvent")
    submission_id = payload.get("submissionId")
    return ChefsEvent(
        form_id=form_id,
        subscription_event=event,
        submission_id=submission_id if isinstance(submission_id, str) else None,
    )


def extract_answers(submission: Any, choice_field: str = "choices") -> tuple[str | None, str | None]:
    """Return ``(choice, email)`` from a CHEFS ``GET /submissions/{id}`` response."""
    data = (
        submission.get("submission", {}).get("submission", {}).get("data", {})
        if isinstance(submission, dict)
        else {}
    )
    choice = data.get(choice_field)
    email = data.get("email")
    return (
        choice if isinstance(choice, str) else None,
        email if isinstance(email, str) and email else None,
    )


def decide_document(choice: str | None) -> str | None:
    return DOCUMENT_BY_CHOICE.get(choice) if choice else None
