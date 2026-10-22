"""CHEFS event-subscription callback (test stage: logs the decision, sends no email).

Exposes:
    POST /hooks/chefs  -> verify token, fetch the submission, log which document applies

Mounted outside the authenticated ``/api/v1`` router: CHEFS is not a TAP user and
authenticates with the shared ``X-Chefs-Token`` header instead. Disabled (404)
until ``CHEFS_WEBHOOK_TOKEN`` is set.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Request

from app.api.errors import ApiError
from app.chefs.events import (
    SUBMISSION_EVENT,
    decide_document,
    extract_answers,
    parse_event,
    token_matches,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

TOKEN_HEADER = "X-Chefs-Token"


async def _fetch_submission(submission_id: str) -> Any:
    # CHEFS gives up on the callback after 10s, so keep the upstream call well under that.
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{settings.CHEFS_API_BASE.rstrip('/')}/submissions/{submission_id}",
            auth=(settings.CHEFS_FORM_ID, settings.CHEFS_API_KEY),
        )
    if response.status_code != 200:
        raise ApiError(502, f"CHEFS submission lookup failed with status {response.status_code}")
    return response.json()


@router.post("/chefs")
async def chefs_event(request: Request) -> dict[str, Any]:
    if not settings.CHEFS_WEBHOOK_TOKEN:
        raise ApiError(404, "Not found")
    if not token_matches(settings.CHEFS_WEBHOOK_TOKEN, request.headers.get(TOKEN_HEADER)):
        raise ApiError(401, "Invalid token")

    try:
        event = parse_event(await request.json())
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc

    if (
        event.subscription_event != SUBMISSION_EVENT
        or event.form_id != settings.CHEFS_FORM_ID
        or not event.submission_id
    ):
        logger.info("CHEFS event ignored: %s for form %s", event.subscription_event, event.form_id)
        return {"status": "ignored"}

    if not settings.CHEFS_API_KEY:
        logger.info("CHEFS submission %s received; no API key, answers not fetched", event.submission_id)
        return {"status": "received", "submissionId": event.submission_id}

    choice, email = extract_answers(await _fetch_submission(event.submission_id))
    document = decide_document(choice)
    # Log the decision, never the submitter's email address.
    logger.info(
        "CHEFS submission %s: choice=%s -> would send %s (email %s)",
        event.submission_id,
        choice,
        f"document {document}" if document else "nothing",
        "present" if email else "missing",
    )
    return {
        "status": "processed",
        "submissionId": event.submission_id,
        "choice": choice,
        "document": document,
        "hasEmail": email is not None,
    }
