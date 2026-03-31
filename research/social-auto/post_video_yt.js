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

  const browser = await chromium.launch({ 
    headless: false, 
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  // To avoid the login wall, we connect to the same userDataDir that openclaw uses, OR we just instruct the user to run it via the openclaw tool. Let's just exit for now and I will run it via openclaw browser tool.
  await browser.close();
  console.log("Use OpenClaw Browser Tool to upload.");
})();
