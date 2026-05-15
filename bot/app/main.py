"""FastAPI app: serves the chat widget, the /chat and /lead endpoints,
the Telegram webhook, and an admin /leads listing."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from telegram import Update

from . import telegram_bot
from .brain import chat as brain_chat
from .config import get_settings
from .knowledge import WELCOME_MESSAGE
from .leads import init_db, list_leads, save_lead
from .notify import notify_new_lead
from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    LeadRecord,
    LeadRequest,
    LeadResponse,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("ebby")


WIDGET_PATH = Path(__file__).resolve().parent.parent / "widget" / "ebby-chat.js"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_INDEX_CANDIDATES = (
    REPO_ROOT / "dist" / "index.html",
    REPO_ROOT / "index.html",
)


def _marketing_index() -> Path | None:
    for path in SITE_INDEX_CANDIDATES:
        if path.is_file():
            return path
    return None


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    log.info("SQLite initialized.")
    await telegram_bot.startup()
    try:
        yield
    finally:
        await telegram_bot.shutdown()


def _make_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="EBBY Bot API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    return app


app = _make_app()


def require_admin(authorization: str = Header(default="")) -> None:
    s = get_settings()
    expected = f"Bearer {s.admin_api_token}"
    if not s.admin_api_token or authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    s = get_settings()
    return HealthResponse(
        status="ok",
        telegram=s.telegram_enabled,
        smtp=s.smtp_enabled,
        model=s.groq_model if s.groq_api_key else None,
    )


@app.get("/")
async def site_root():
    """Marketing site at / when dist/ or index.html exists; else API discovery JSON."""
    index = _marketing_index()
    if index is not None:
        return FileResponse(index, media_type="text/html")
    return {
        "name": "EBBY Bot API",
        "endpoints": ["/health", "/chat", "/lead", "/widget/ebby-chat.js"],
        "welcome": WELCOME_MESSAGE,
        "hint": "Run `node scripts/build-static.mjs` from repo root for the marketing page.",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    reply, captured = await brain_chat(
        session_id=req.session_id,
        user_message=req.message,
        source="web",
    )
    return ChatResponse(reply=reply, lead_captured=captured)


@app.post("/lead", response_model=LeadResponse)
async def lead_endpoint(req: LeadRequest) -> LeadResponse:
    try:
        lead_id = save_lead(
            name=req.name.strip(),
            phone=req.phone.strip(),
            email=str(req.email).strip(),
            service=req.service.strip(),
            details=req.details.strip(),
            source=req.source or "website-form",
        )
    except Exception:
        log.exception("save_lead failed")
        raise HTTPException(status_code=500, detail="storage-error")
    try:
        await notify_new_lead(
            lead_id=lead_id,
            name=req.name.strip(),
            phone=req.phone.strip(),
            email=str(req.email).strip(),
            service=req.service.strip(),
            details=req.details.strip(),
            source=req.source or "website-form",
        )
    except Exception:
        log.exception("notify_new_lead failed (lead still saved)")
    return LeadResponse(id=lead_id, ok=True)


@app.get("/leads", response_model=List[LeadRecord], dependencies=[Depends(require_admin)])
async def leads_endpoint(limit: int = 100) -> List[LeadRecord]:
    return list_leads(limit=limit)


@app.get("/widget/ebby-chat.js")
async def widget_js() -> FileResponse:
    if not WIDGET_PATH.is_file():
        raise HTTPException(status_code=404, detail="widget not found")
    return FileResponse(
        WIDGET_PATH,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> JSONResponse:
    s = get_settings()
    if not s.telegram_enabled:
        raise HTTPException(status_code=404, detail="telegram disabled")
    if secret != s.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="bad secret")
    application = telegram_bot.get_application()
    if application is None:
        raise HTTPException(status_code=503, detail="telegram not ready")
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")
    update = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return JSONResponse({"ok": True})


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots() -> str:
    return "User-agent: *\nDisallow:\n"
