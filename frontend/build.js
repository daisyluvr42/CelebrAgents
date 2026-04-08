// Simple build script: copies files to dist/ and injects API URL
const fs = require("fs");
const path = require("path");

const dist = path.join(__dirname, "dist");
fs.mkdirSync(dist, { recursive: true });

const apiUrl = process.env.API_URL || "";

// Copy all files except build artifacts
const files = ["index.html", "style.css", "app.js"];
for (const file of files) {
  fs.copyFileSync(path.join(__dirname, file), path.join(dist, file));
}

// Generate config.js with injected API URL
fs.writeFileSync(
  path.join(dist, "config.js"),
  `window.CELEBR_API = "${apiUrl}";\n`
);

console.log(`Built to dist/ with API_URL=${apiUrl || "(same origin)"}`);
