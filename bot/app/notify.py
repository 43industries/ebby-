"""Lead notifications: Telegram DM (primary) + optional SMTP email.

Both channels fail gracefully - missing credentials simply skip that
channel rather than raising, so a misconfigured environment still saves
the lead.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

import httpx

from .config import get_settings


log = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


def _format_lead_message(
    *,
    lead_id: int,
    name: str,
    phone: str,
    email: str,
    service: str,
    details: str,
    source: str,
) -> str:
    return (
        "New EBBY lead\n"
        f"Lead #{lead_id} ({source})\n\n"
        f"Name:    {name}\n"
        f"Phone:   {phone}\n"
        f"Email:   {email}\n"
        f"Service: {service}\n\n"
        f"Details:\n{details}"
    )


async def send_admin_telegram(text: str) -> bool:
    """Send `text` to the admin chat. Returns True on success."""
    s = get_settings()
    if not s.telegram_bot_token or not s.admin_chat_id:
        log.info("Telegram admin notify skipped (token or chat id missing)")
        return False
    url = f"{TELEGRAM_API}/bot{s.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                url,
                json={
                    "chat_id": s.admin_chat_id,
                    "text": text,
                    "disable_web_page_preview": True,
                },
            )
            if r.status_code != 200:
                log.warning("Telegram notify failed: %s %s", r.status_code, r.text)
                return False
            return True
    except Exception:
        log.exception("Telegram notify raised")
        return False


def send_email(subject: str, body: str) -> bool:
    """Send a plain-text email via SMTP. No-op if SMTP isn't configured."""
    s = get_settings()
    if not s.smtp_enabled:
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = s.smtp_from
    msg["To"] = s.smtp_to
    msg.set_content(body)
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            if s.smtp_user and s.smtp_password:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
        return True
    except Exception:
        log.exception("SMTP send failed")
        return False


async def notify_new_lead(
    *,
    lead_id: int,
    name: str,
    phone: str,
    email: str,
    service: str,
    details: str,
    source: str,
) -> None:
    text = _format_lead_message(
        lead_id=lead_id,
        name=name,
        phone=phone,
        email=email,
        service=service,
        details=details,
        source=source,
    )
    await send_admin_telegram(text)
    send_email(subject=f"New EBBY lead #{lead_id} - {name}", body=text)


async def send_user_telegram(chat_id: int | str, text: str) -> Optional[int]:
    """Used by the Telegram bot path to send a reply to a specific user."""
    s = get_settings()
    if not s.telegram_bot_token:
        return None
    url = f"{TELEGRAM_API}/bot{s.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "disable_web_page_preview": True,
                },
            )
            if r.status_code != 200:
                log.warning("Telegram reply failed: %s %s", r.status_code, r.text)
                return None
            return r.json().get("result", {}).get("message_id")
    except Exception:
        log.exception("Telegram reply raised")
        return None
