# EBBY Bot

One Python backend that powers three faces of the same assistant:

1. A **chat widget** on the EBBY website (`INDEX.HTML`).
2. A **Telegram bot** that mirrors the website assistant.
3. The **lead handler** behind the website's contact form.

All three share the same knowledge base and lead store.

```
[Site widget]   [Telegram users]
       \              /
        \            /
       FastAPI backend
       /     |      \
   Groq   SQLite   Notifier (Telegram DM + optional SMTP)
```

## What you need

- Python 3.10+
- A free [Groq](https://console.groq.com) API key (no card required) - powers the chat brain.
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- (Optional) A public HTTPS URL once you deploy (Render free tier works fine).

## 1. Local setup

```bash
cd bot
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `.env` and fill in at least:

- `GROQ_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_CHAT_ID` (see below for how to find it)

### Get your Telegram admin chat id

1. In Telegram, find your new bot and send it any message (e.g. `hi`).
2. In a browser, open:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. Copy the value of `result[0].message.chat.id` into `ADMIN_CHAT_ID`.

That's the chat the backend will DM you in whenever a new lead comes in.

## 2. Run the API locally

```bash
cd bot
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/health - you should see something like:

```json
{ "status": "ok", "telegram": true, "smtp": false, "model": "llama-3.1-8b-instant" }
```

The widget script is served at http://localhost:8000/widget/ebby-chat.js.

### Try the website end-to-end

`INDEX.HTML` is already wired to the local API. Just open it in your
browser (double-click the file or use a tiny static server):

```bash
# from the project root, in another terminal:
python -m http.server 5500
# then visit http://localhost:5500/INDEX.HTML
```

You should see:

- A floating purple chat bubble in the bottom-right.
- The contact form posts to the API and shows the success toast.
- A Telegram DM hits your admin chat for every lead saved.

### Try Telegram locally (no public URL needed)

Stop the uvicorn process, then:

```bash
cd bot
python -m scripts.poll
```

This runs the Telegram bot in long-polling mode. Open Telegram, message
your bot, and you should get replies from the same brain. (Don't run
both `uvicorn` and `poll.py` at the same time - Telegram only allows
one consumer per bot.)

## 3. Deploy to Render (free tier)

1. Push the `bot/` folder to a GitHub repo.
2. On Render, create a new **Web Service** pointing at the repo.
   - Root directory: `bot`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - (Or just rely on the included `Procfile`.)
3. Add the env vars from your `.env` to the Render service (set
   `PUBLIC_BASE_URL` to your `https://<name>.onrender.com` URL and
   `ALLOWED_ORIGINS` to your real site origin).
4. Deploy. The lifespan hook will register the Telegram webhook
   automatically when `PUBLIC_BASE_URL` is set.

If you ever need to manage the webhook by hand:

```bash
# Register
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-render>.onrender.com/telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>"

# Inspect
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Remove
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

## 4. Point the website at production

In `INDEX.HTML`, find the EBBY Bot integration block near the bottom:

```html
<script>
  window.EBBY_API = "http://localhost:8000";
</script>
<script src="http://localhost:8000/widget/ebby-chat.js" defer></script>
```

Change both URLs to your Render URL, e.g. `https://ebby-bot.onrender.com`.

## 5. View leads

```bash
curl -H "Authorization: Bearer <ADMIN_API_TOKEN>" \
     https://<your-render>.onrender.com/leads
```

Returns the most recent leads as JSON. (A simple admin UI is the
obvious follow-up.)

## File map

| Path                                | What it does                                                  |
| ----------------------------------- | ------------------------------------------------------------- |
| `app/main.py`                       | FastAPI app, routes, lifespan                                 |
| `app/config.py`                     | Settings loaded from env / `.env`                             |
| `app/knowledge.py`                  | Static EBBY knowledge + system prompt + tool schema           |
| `app/brain.py`                      | Groq client, per-session history, lead tool-call loop         |
| `app/leads.py`                      | SQLite schema + `save_lead` / `list_leads`                    |
| `app/notify.py`                     | Telegram admin DM + optional SMTP                             |
| `app/telegram_bot.py`               | python-telegram-bot Application + webhook setup               |
| `app/schemas.py`                    | Pydantic request / response models                            |
| `widget/ebby-chat.js`               | Floating chat bubble injected into the website                |
| `scripts/poll.py`                   | Run the Telegram bot in polling mode for local dev            |

## Updating the bot's knowledge

The website copy lives in `INDEX.HTML`. The bot's view of the world
lives in [`app/knowledge.py`](app/knowledge.py). When you update prices,
services, or the process on the site, also update `EBBY_KNOWLEDGE` in
that file so the bot stays in sync.
