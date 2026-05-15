/**
 * Render static-site build: inject bot API URL into index.html.
 * EBBY_API_URL is set from ebby-bot's RENDER_EXTERNAL_URL via render.yaml.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const indexPath = path.join(root, "index.html");

const placeholder = "https://your-ebby-bot.onrender.com";
const url = (process.env.EBBY_API_URL || "").trim().replace(/\/+$/, "");

let html = fs.readFileSync(indexPath, "utf8");

if (!url) {
  console.log("inject-ebby-api: EBBY_API_URL unset — leaving placeholder in index.html");
  process.exit(0);
}

if (!html.includes(placeholder)) {
  console.warn("inject-ebby-api: placeholder not found; no changes made");
  process.exit(0);
}

html = html.replaceAll(placeholder, url);
fs.writeFileSync(indexPath, html, "utf8");
console.log(`inject-ebby-api: set window.EBBY_API → ${url}`);
