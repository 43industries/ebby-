"""Run the Telegram bot in polling mode for local development.

Use this when you don't have a public HTTPS URL yet. Make sure your
.env has TELEGRAM_BOT_TOKEN, GROQ_API_KEY (and ADMIN_CHAT_ID for
notifications).

    python -m scripts.poll

Run this INSTEAD of `uvicorn app.main:app` (don't run both - Telegram
only allows one consumer at a time).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.leads import init_db  # noqa: E402
from app.telegram_bot import build_application  # noqa: E402


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    s = get_settings()
    if not s.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN missing in .env")
    init_db()
    app = build_application()
    print("Polling Telegram. Ctrl+C to stop.")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
