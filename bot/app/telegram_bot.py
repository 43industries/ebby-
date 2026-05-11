"""Telegram integration via python-telegram-bot.

Builds an Application that reuses the same `brain.chat()` used by the
website widget, so both channels share knowledge, history shape, and
lead capture behavior.
"""

from __future__ import annotations

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import brain
from .config import get_settings
from .knowledge import COMPANY_NAME, WELCOME_MESSAGE


log = logging.getLogger(__name__)

_application: Optional[Application] = None


def _session_id_for(update: Update) -> str:
    chat = update.effective_chat
    return f"tg:{chat.id}" if chat else "tg:unknown"


async def _start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    user = update.effective_user
    name = user.first_name if user and user.first_name else "there"
    await update.effective_chat.send_message(
        f"Hi {name}! {WELCOME_MESSAGE}\n\n"
        "Try asking about our services, pricing, or how we work."
    )
    brain.sessions.reset(_session_id_for(update))


async def _help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    await update.effective_chat.send_message(
        f"I'm the {COMPANY_NAME} assistant. Ask me about:\n"
        "- Services we offer\n"
        "- Pricing (Starter / Business / Enterprise)\n"
        "- How we work\n"
        "Or tell me about your project and I'll set up a call.\n\n"
        "Commands: /start, /reset, /help"
    )


async def _reset(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    brain.sessions.reset(_session_id_for(update))
    await update.effective_chat.send_message("Conversation reset. What's next?")


async def _on_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None or update.message is None:
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    await update.effective_chat.send_chat_action("typing")
    try:
        reply, _captured = await brain.chat(
            session_id=_session_id_for(update),
            user_message=text,
            source="telegram",
        )
    except Exception:
        log.exception("brain.chat failed in telegram handler")
        reply = brain.FALLBACK_MESSAGE
    await update.effective_chat.send_message(reply)


def build_application() -> Application:
    s = get_settings()
    if not s.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    app = ApplicationBuilder().token(s.telegram_bot_token).updater(None).build()
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CommandHandler("help", _help))
    app.add_handler(CommandHandler("reset", _reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))
    return app


def _is_placeholder_token(token: str) -> bool:
    """Detect the example token shipped in .env.example so we skip cleanly."""
    if not token:
        return True
    lowered = token.lower()
    return (
        "your-telegram-bot-token" in lowered
        or "xxxx" in lowered
        or token.startswith("123456789:AA-")
    )


async def startup() -> Optional[Application]:
    """Initialize PTB and (if PUBLIC_BASE_URL is set) register the webhook.

    Failures here are logged but never raised - the rest of the API
    (chat widget, /lead, /health) must keep working even if Telegram
    is misconfigured.
    """
    global _application
    s = get_settings()
    if not s.telegram_enabled:
        log.info("Telegram disabled (no TELEGRAM_BOT_TOKEN).")
        return None
    if _is_placeholder_token(s.telegram_bot_token):
        log.warning(
            "TELEGRAM_BOT_TOKEN looks like the placeholder from .env.example - "
            "skipping Telegram setup. Update .env with a real token from @BotFather."
        )
        return None
    try:
        _application = build_application()
        await _application.initialize()
        await _application.start()
    except Exception:
        log.exception("Telegram initialization failed - continuing without Telegram")
        try:
            if _application is not None:
                await _application.shutdown()
        except Exception:
            log.exception("Telegram shutdown after failed init also raised")
        _application = None
        return None

    if s.public_base_url:
        url = f"{s.public_base_url.rstrip('/')}/telegram/webhook/{s.telegram_webhook_secret}"
        try:
            await _application.bot.set_webhook(
                url=url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            log.info("Telegram webhook registered: %s", url)
        except Exception:
            log.exception("Failed to set Telegram webhook")
    else:
        log.info(
            "PUBLIC_BASE_URL not set; Telegram webhook NOT registered. "
            "Run scripts/poll.py for local development if you want polling."
        )
    return _application


async def shutdown() -> None:
    global _application
    if _application is None:
        return
    try:
        await _application.stop()
        await _application.shutdown()
    finally:
        _application = None


def get_application() -> Optional[Application]:
    return _application
