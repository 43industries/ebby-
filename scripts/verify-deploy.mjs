/**
 * Verify unified Render deploy (site at /, bot at /health).
 * Usage: node scripts/verify-deploy.mjs https://ebby-xxxx.onrender.com
 */
const marker = "Turning Ideas Into Working Digital Products";
const base = (process.argv[2] ?? process.env.EBBY_SITE_URL ?? "").trim().replace(/\/+$/, "");

if (!base) {
  console.error("verify-deploy: pass your Render URL");
  process.exit(2);
}

const home = await fetch(base, {
  redirect: "follow",
  headers: { "user-agent": "ebby-verify-deploy/1" },
});
if (!home.ok) {
  console.error(`verify-deploy: site HTTP ${home.status}`);
  process.exit(1);
}
const html = await home.text();
if (!html.includes(marker)) {
  console.error("verify-deploy: / is not the EBBY marketing page");
  process.exit(1);
}

const health = await fetch(`${base}/health`, {
  headers: { "user-agent": "ebby-verify-deploy/1" },
});
if (!health.ok) {
  console.error(`verify-deploy: /health HTTP ${health.status}`);
  process.exit(1);
}
const data = await health.json();
if (data.status !== "ok") {
  console.error("verify-deploy: bad health payload", data);
  process.exit(1);
}

console.log(`verify-deploy: OK — ${base}`);
if (!data.model) {
  console.warn("verify-deploy: add GROQ_API_KEY on Render for chat to work");
}
