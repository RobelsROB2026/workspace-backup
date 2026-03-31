const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs = require('fs');
const path = require('path');

// Pass input file via args, fallback to daily prep
const inputFile = process.argv[2] || path.join(process.env.HOME, 'research/social-auto/barry_prepped_post.json');
const randomDelay = (min, max) => new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1) + min)));

(async () => {
  if (!fs.existsSync(inputFile)) {
    console.error("No input post found at " + inputFile);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  const localPath = data.local_path;
  const caption = data.caption;
  const shortTitle = data.title || "Barry Hauler 🚛💨 #shorts #trucking";

  console.log(`Uploading to YouTube Shorts via Web UI: ${localPath}`);
  console.log(`OpenClaw is bypassing to manual upload...`);
})();
