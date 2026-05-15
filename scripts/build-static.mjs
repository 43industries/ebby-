/**
 * Render static-site build: copy index.html to dist/ and inject bot API URL.
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
  console.log(`build-static: injected EBBY_API → ${url}`);
} else if (!url) {
  console.log("build-static: EBBY_API_URL unset — dist will use placeholder");
} else {
  console.warn("build-static: placeholder not found in index.html");
}

fs.mkdirSync(distDir, { recursive: true });
fs.writeFileSync(outPath, html, "utf8");
console.log(`build-static: wrote ${outPath}`);
