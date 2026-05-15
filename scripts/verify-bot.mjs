/**
 * Check deployed bot health. Usage:
 *   node scripts/verify-bot.mjs https://ebby-bot-xxxx.onrender.com
 *   EBBY_API_URL=https://... npm run verify:bot
 */
const base = (process.argv[2] ?? process.env.EBBY_API_URL ?? "").trim().replace(/\/+$/, "");

if (!base) {
  console.error("verify-bot: pass API base URL or set EBBY_API_URL");
  process.exit(2);
}

const res = await fetch(`${base}/health`, {
  headers: { "user-agent": "ebby-verify-bot/1" },
});

if (!res.ok) {
  console.error(`verify-bot: HTTP ${res.status} for ${base}/health`);
  process.exit(1);
}

const data = await res.json();
if (data.status !== "ok") {
  console.error("verify-bot: unexpected health payload", data);
  process.exit(1);
}

console.log(`verify-bot: OK — ${base}/health`, data);
if (!data.model) {
  console.warn("verify-bot: GROQ_API_KEY may be missing (model is null)");
}
