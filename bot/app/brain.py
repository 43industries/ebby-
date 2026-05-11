"""LLM brain shared by the website widget and the Telegram bot.

Uses Groq's OpenAI-compatible REST API directly via httpx so we avoid an
extra SDK dependency. Implements a single tool, `capture_lead`, which
saves a lead and notifies the admin.
"""

from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import httpx

from .config import get_settings
from .knowledge import CAPTURE_LEAD_TOOL, SYSTEM_PROMPT
from .leads import save_lead
from .notify import notify_new_lead


log = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_HISTORY_TURNS = 12
SESSION_TTL_SECONDS = 60 * 60 * 6
MAX_SESSIONS = 1000
MAX_TOOL_HOPS = 3
REQUEST_TIMEOUT = 30.0

FALLBACK_MESSAGE = (
    "Sorry, I'm having trouble reaching my brain right now. Please try again "
    "in a moment, or use the contact form to reach the EBBY team directly."
)


@dataclass
class Session:
    history: List[Dict[str, Any]] = field(default_factory=list)
    lead_captured: bool = False
    last_seen: float = field(default_factory=time.time)


class SessionStore:
    """Tiny LRU-ish in-memory store. Fine for a single-instance deployment."""

    def __init__(self, max_sessions: int = MAX_SESSIONS) -> None:
        self._sessions: "OrderedDict[str, Session]" = OrderedDict()
        self._max = max_sessions

    def get(self, session_id: str) -> Session:
        now = time.time()
        s = self._sessions.get(session_id)
        if s is None or now - s.last_seen > SESSION_TTL_SECONDS:
            s = Session()
            self._sessions[session_id] = s
        else:
            self._sessions.move_to_end(session_id)
        s.last_seen = now
        while len(self._sessions) > self._max:
            self._sessions.popitem(last=False)
        return s

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


sessions = SessionStore()


def _trim_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the last MAX_HISTORY_TURNS user/assistant turns plus their tool messages."""
    if len(history) <= MAX_HISTORY_TURNS * 2:
        return history
    user_indices = [i for i, m in enumerate(history) if m.get("role") == "user"]
    if len(user_indices) <= MAX_HISTORY_TURNS:
        return history
    cut = user_indices[-MAX_HISTORY_TURNS]
    return history[cut:]


async def _call_groq(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    s = get_settings()
    if not s.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    payload = {
        "model": s.groq_model,
        "messages": messages,
        "tools": [CAPTURE_LEAD_TOOL],
        "tool_choice": "auto",
        "temperature": 0.4,
        "max_tokens": 700,
    }
    headers = {
        "Authorization": f"Bearer {s.groq_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        r = await client.post(GROQ_URL, json=payload, headers=headers)
        if r.status_code >= 400:
            log.warning("Groq error %s: %s", r.status_code, r.text)
            r.raise_for_status()
        return r.json()


async def _run_capture_lead(args: Dict[str, Any], source: str) -> Tuple[str, bool]:
    """Persist the lead and notify; return the tool result string and a flag."""
    required = ["name", "phone", "email", "service", "details"]
    missing = [k for k in required if not str(args.get(k, "")).strip()]
    if missing:
        return (
            json.dumps({"ok": False, "error": f"missing fields: {', '.join(missing)}"}),
            False,
        )
    try:
        lead_id = save_lead(
            name=str(args["name"]).strip(),
            phone=str(args["phone"]).strip(),
            email=str(args["email"]).strip(),
            service=str(args["service"]).strip(),
            details=str(args["details"]).strip(),
            source=source,
        )
    except Exception:
        log.exception("save_lead failed")
        return json.dumps({"ok": False, "error": "internal-storage-error"}), False
    try:
        await notify_new_lead(
            lead_id=lead_id,
            name=str(args["name"]).strip(),
            phone=str(args["phone"]).strip(),
            email=str(args["email"]).strip(),
            service=str(args["service"]).strip(),
            details=str(args["details"]).strip(),
            source=source,
        )
    except Exception:
        log.exception("notify_new_lead failed (lead still saved)")
    return (
        json.dumps(
            {
                "ok": True,
                "lead_id": lead_id,
                "message": "Lead saved. EBBY team notified.",
            }
        ),
        True,
    )


async def chat(session_id: str, user_message: str, *, source: str = "web") -> Tuple[str, bool]:
    """Run a single user turn through the LLM, handling tool calls.

    Returns `(reply_text, lead_captured_this_turn)`.
    """
    sess = sessions.get(session_id)

    sess.history.append({"role": "user", "content": user_message})
    sess.history = _trim_history(sess.history)

    messages: List[Dict[str, Any]] = (
        [{"role": "system", "content": SYSTEM_PROMPT}] + sess.history
    )

    captured_now = False
    final_text = ""

    for hop in range(MAX_TOOL_HOPS):
        try:
            data = await _call_groq(messages)
        except Exception:
            log.exception("Groq call failed")
            return FALLBACK_MESSAGE, False

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        content = (msg.get("content") or "").strip()

        if tool_calls:
            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)
            sess.history.append(assistant_msg)

            for call in tool_calls:
                fn = (call.get("function") or {}).get("name")
                raw_args = (call.get("function") or {}).get("arguments") or "{}"
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
                if fn == "capture_lead":
                    result, ok = await _run_capture_lead(args, source=source)
                    if ok:
                        captured_now = True
                        sess.lead_captured = True
                else:
                    result = json.dumps({"ok": False, "error": "unknown tool"})
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "name": fn,
                    "content": result,
                }
                messages.append(tool_msg)
                sess.history.append(tool_msg)
            continue

        final_text = content or "..."
        sess.history.append({"role": "assistant", "content": final_text})
        break
    else:
        final_text = (
            "Got it. I'll pass this along to the EBBY team and they'll be in touch."
        )
        sess.history.append({"role": "assistant", "content": final_text})

    sess.history = _trim_history(sess.history)
    return final_text, captured_now
