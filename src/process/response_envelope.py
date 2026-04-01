"""Parse LLM JSON responses with mandatory missing_context envelope."""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MissingContextHalt(Exception):
    """Raised when missing_context is true; pipeline must stop (operator restarts manually)."""

    def __init__(self, track_name: str, missing: list, detail: str):
        self.track_name = track_name
        self.missing = missing
        self.detail = detail
        super().__init__(f"[{track_name}] missing context: {missing}")


def parse_envelope(content: str) -> dict[str, Any]:
    """Parse JSON; must be a single object."""
    return json.loads(content)


def unwrap_payload(parsed: dict[str, Any], track_name: str) -> dict[str, Any]:
    """
    If missing_context is true, notify Telegram and raise MissingContextHalt.
    Otherwise return the inner payload object.
    """
    if "missing_context" not in parsed:
        raise ValueError(
            'LLM response must include top-level "missing_context" (boolean). '
            f"Keys seen: {list(parsed.keys())[:20]}"
        )

    if parsed["missing_context"] is True:
        missing = parsed.get("missing") or []
        if not isinstance(missing, list):
            missing = [str(missing)]
        detail = str(parsed.get("detail") or "")
        try:
            from src.notify.telegram import send_missing_context_alert

            send_missing_context_alert(
                track_name=track_name,
                missing=missing,
                detail=detail,
            )
        except Exception as e:
            logger.error(f"Failed to send missing-context Telegram: {e}")
        raise MissingContextHalt(track_name, missing, detail)

    if parsed.get("missing_context") is not False:
        raise ValueError(f'Expected missing_context false, got: {parsed.get("missing_context")!r}')

    payload = parsed.get("payload")
    if payload is None:
        raise ValueError('When missing_context is false, "payload" must be a JSON object (not null).')
    if not isinstance(payload, dict):
        raise ValueError(f'"payload" must be an object, got {type(payload).__name__}')
    return payload
