"""CHEFS event-subscription helpers: token check, payload parsing, document choice."""
import pytest

from app.chefs.events import (
    SUBMISSION_EVENT,
    decide_document,
    extract_answers,
    parse_event,
    token_matches,
)


# ---- token_matches ----------------------------------------------------------


def test_token_matches_exact_value() -> None:
    assert token_matches("s3cret", "s3cret")


@pytest.mark.parametrize("received", [None, "", "S3CRET", "s3cret ", "other"])
def test_token_rejects_missing_or_different_value(received) -> None:
    assert not token_matches("s3cret", received)


def test_token_rejects_everything_when_not_configured() -> None:
    assert not token_matches("", "")


# ---- parse_event ------------------------------------------------------------


def test_parse_submission_event() -> None:
    event = parse_event(
        {
            "formId": "form-1",
            "formVersion": "ver-1",
            "subscriptionEvent": SUBMISSION_EVENT,
            "submissionId": "sub-1",
        }
    )
    assert event.form_id == "form-1"
    assert event.subscription_event == SUBMISSION_EVENT
    assert event.submission_id == "sub-1"


def test_parse_publish_event_has_no_submission() -> None:
    event = parse_event({"formId": "form-1", "subscriptionEvent": "eventFormPublished"})
    assert event.submission_id is None


@pytest.mark.parametrize("payload", [None, [], "x", {}, {"formId": "form-1"}, {"subscriptionEvent": "e"}])
def test_parse_rejects_malformed_payload(payload) -> None:
    with pytest.raises(ValueError):
        parse_event(payload)


# ---- extract_answers / decide_document --------------------------------------


def _submission(data: dict) -> dict:
    return {"submission": {"submission": {"data": data}}}


def test_extract_answers_reads_choice_and_email() -> None:
    assert extract_answers(_submission({"choices": "typeA", "email": "a@example.com"})) == (
        "typeA",
        "a@example.com",
    )


@pytest.mark.parametrize("response", [None, {}, {"submission": {}}, _submission({})])
def test_extract_answers_tolerates_missing_fields(response) -> None:
    assert extract_answers(response) == (None, None)


def test_extract_answers_treats_blank_email_as_missing() -> None:
    assert extract_answers(_submission({"choices": "none", "email": ""})) == ("none", None)


@pytest.mark.parametrize(
    ("choice", "document"),
    [("typeA", "A"), ("typeB", "B"), ("none", None), (None, None), ("Type A", None)],
)
def test_decide_document(choice, document) -> None:
    assert decide_document(choice) == document
