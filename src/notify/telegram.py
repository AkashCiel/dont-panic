"""Telegram Bot API notification functions."""
import logging
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _get_credentials() -> tuple[str, str]:
    """Get Telegram credentials from config."""
    from src.config import get_config
    cfg = get_config()
    return cfg.telegram_bot_token, cfg.telegram_chat_id


def _send(token: str, chat_id: str, text: str) -> bool:
    """Send a Telegram HTML message. Returns True on success."""
    if not token or not chat_id:
        logger.debug("Telegram not configured — skipping notification")
        return False
    try:
        url = TELEGRAM_SEND_URL.format(token=token)
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_fetch_summary(cycle_id: str, results: list[dict]) -> bool:
    """
    Send fetch cycle summary.

    Format:
        📥 Fetch cycle: 2025-01-15 06:02 UTC
        ✅ 18/20 sources OK
        ⚠️ OpenReview: credentials not configured
        ❌ ARC-AGI leaderboard: Connection timeout
        New items: 147
    """
    token, chat_id = _get_credentials()
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M")

    n_total = len(results)
    n_success = sum(1 for r in results if r.get("status") == "success")
    total_new = sum(r.get("items_found", 0) for r in results)

    lines = [
        f"📥 <b>Fetch cycle:</b> {date_str} UTC",
        f"✅ {n_success}/{n_total} sources OK",
    ]
    for r in results:
        status = r.get("status", "")
        name = r.get("source_name", "?")
        err = (r.get("error_message") or "")[:120]
        if status == "warning":
            lines.append(f"⚠️ {name}: {err}")
        elif status == "error":
            lines.append(f"❌ {name}: {err}")

    lines.append(f"New items: {total_new}")
    return _send(token, chat_id, "\n".join(lines))


def send_high_signal_alert(source_name: str, weight: int, title: str) -> bool:
    """Send alert when a weight ≥ 4 source publishes new content."""
    token, chat_id = _get_credentials()
    text = (
        f"🔔 <b>High-signal update detected</b>\n"
        f"Source: {source_name} (weight {weight})\n"
        f"Title: \"{title[:200]}\""
    )
    return _send(token, chat_id, text)


def send_wave1_summary(
    date: str,
    items: int,
    sources: int,
    claims: int,
    by_criterion: dict,
    cost: float,
    duration_minutes: float,
) -> bool:
    """Send Wave 1 completion summary."""
    token, chat_id = _get_credentials()
    by_crit_str = " | ".join(f"C{k}:{v}" for k, v in sorted(by_criterion.items()))
    text = (
        f"🔬 <b>Wave 1 complete:</b> {date}\n"
        f"Sources processed: {items} items from {sources} sources\n"
        f"Claims extracted: {claims}\n"
        f"By criterion: {by_crit_str}\n"
        f"Batch API cost: ${cost:.4f}\n"
        f"Duration: {duration_minutes:.1f} min"
    )
    return _send(token, chat_id, text)


def send_wave2_summary(
    date: str,
    scenario: str,
    report_url: str,
    cost: float,
    duration_minutes: float,
) -> bool:
    """Send Wave 2 / report generation summary."""
    token, chat_id = _get_credentials()
    text = (
        f"📊 <b>Report generated:</b> {date}\n"
        f"Scenario assessment: <b>{scenario}</b>\n"
        f"Report URL: {report_url}\n"
        f"Batch API cost: ${cost:.4f}\n"
        f"Duration: {duration_minutes:.1f} min"
    )
    return _send(token, chat_id, text)


def send_missing_context_alert(track_name: str, missing: list, detail: str) -> bool:
    """
    Notify when an LLM returns missing_context: true.
    Message contains only: track_name, missing, detail (per product requirement).
    """
    token, chat_id = _get_credentials()
    missing_str = ", ".join(str(m) for m in missing) if missing else ""
    text = (
        f"<b>track_name</b>\n{track_name}\n\n"
        f"<b>missing</b>\n{missing_str}\n\n"
        f"<b>detail</b>\n{detail[:8000]}"
    )
    return _send(token, chat_id, text)


def send_error(step: str, error_message: str) -> bool:
    """Send an error notification for a failed pipeline step."""
    token, chat_id = _get_credentials()
    text = f"❌ <b>Error in {step}</b>\n{error_message[:500]}"
    return _send(token, chat_id, text)


def send_diffusion_fetch_summary(cycle_id: str, results: list[dict]) -> bool:
    """Diffusion-only fetch summary (🌐 prefix)."""
    token, chat_id = _get_credentials()
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M")
    n_total = len(results)
    n_success = sum(1 for r in results if r.get("status") == "success")
    total_new = sum(r.get("items_found", 0) for r in results)
    lines = [
        f"🌐 <b>Diffusion fetch:</b> {date_str} UTC",
        f"✅ {n_success}/{n_total} sources OK",
    ]
    for r in results:
        status = r.get("status", "")
        name = r.get("source_name", "?")
        err = (r.get("error_message") or "")[:120]
        if status == "error":
            lines.append(f"❌ {name}: {err}")
    lines.append(f"New items: {total_new}")
    return _send(token, chat_id, "\n".join(lines))


def send_diffusion_wave1_summary(
    date: str,
    items: int,
    findings: int,
    cost: float,
    duration_minutes: float,
) -> bool:
    token, chat_id = _get_credentials()
    text = (
        f"🌐 <b>Diffusion Wave 1:</b> {date}\n"
        f"Items in queue: {items}\n"
        f"Findings extracted: {findings}\n"
        f"Batch API cost: ${cost:.4f}\n"
        f"Duration: {duration_minutes:.1f} min"
    )
    return _send(token, chat_id, text)


def send_diffusion_wave2_summary(
    date: str,
    report_url: str,
    cost: float,
    duration_minutes: float,
) -> bool:
    token, chat_id = _get_credentials()
    text = (
        f"🌐 <b>Diffusion report generated:</b> {date}\n"
        f"Report URL: {report_url}\n"
        f"Batch API cost: ${cost:.4f}\n"
        f"Duration: {duration_minutes:.1f} min"
    )
    return _send(token, chat_id, text)
