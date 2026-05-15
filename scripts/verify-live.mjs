/**
 * Check that a deployed URL serves this repo's marketing page (unique title marker).
 * Usage: node scripts/verify-live.mjs https://ebby-site.onrender.com
 *    or: EBBY_SITE_URL=https://... npm run verify:live
 */
const marker = "Turning Ideas Into Working Digital Products";
const url = process.argv[2] ?? process.env.EBBY_SITE_URL;

if (!url || String(url).trim() === "") {
  console.error(
    "verify-live: pass a URL (e.g. node scripts/verify-live.mjs https://<site>.onrender.com)\n" +
      "         or set EBBY_SITE_URL (Render → ebby-site → URL)."
  );
  process.exit(2);
}

const res = await fetch(String(url).trim(), {
  redirect: "follow",
  headers: { "user-agent": "ebby-verify-live/1" },
});

if (!res.ok) {
  console.error(`verify-live: HTTP ${res.status} for ${url}`);
  process.exit(1);
}

const text = await res.text();
if (!text.includes(marker)) {
  console.error(
    "verify-live: response did not contain the EBBY landing page marker.\n" +
      "         Wrong URL, not deployed yet, or a different site at that host."
  );
  process.exit(1);
}

console.log(`verify-live: OK — ${url} serves the EBBY marketing page.`);
