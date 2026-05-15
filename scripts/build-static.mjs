/**
 * Copy index.html → dist/ for production. API URL:
 * - EBBY_API_URL set → inject that URL (split-host deploy)
 * - unset → same-origin (single Render service; browser uses location.origin)
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const srcPath = path.join(root, "index.html");
const distDir = path.join(root, "dist");
const outPath = path.join(distDir, "index.html");

const placeholder = "https://your-ebby-bot.onrender.com";
const url = (process.env.EBBY_API_URL || "").trim().replace(/\/+$/, "");

let html = fs.readFileSync(srcPath, "utf8");

if (url && html.includes(placeholder)) {
  html = html.replaceAll(placeholder, url);
  console.log(`build-static: EBBY_API → ${url}`);
} else if (html.includes(placeholder)) {
  html = html.replace(
    `window.EBBY_API = "${placeholder}";`,
    "window.EBBY_API = \"\"; // same host as API on Render"
  );
  console.log("build-static: same-origin API (empty EBBY_API)");
}

fs.mkdirSync(distDir, { recursive: true });
fs.writeFileSync(outPath, html, "utf8");
console.log(`build-static: wrote ${outPath}`);
