const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs = require('fs');
const path = require('path');

const caption = process.argv[2];
const mediaPath = process.argv[3];
const userDataDir = '/Users/roba/.openclaw/browser/profiles/openclaw/';

const randomDelay = (min, max) => new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1) + min)));

(async () => {
  console.log(`Launching browser with profile: ${userDataDir}`);
  const browser = await chromium.launchPersistentContext(userDataDir, {
    headless: false, // Stealth
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  try {
    console.log("Navigating to x.com/compose/post...");
    await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(10000, 15000);

    // Take screenshot to verify state
    await page.screenshot({ path: '/tmp/post_init.png' });
    console.log("Screenshot taken: /tmp/post_init.png");

    // Click the compose box to ensure focus
    const textBox = await page.waitForSelector('div[data-testid="tweetTextarea_0"]', { timeout: 30000 });
    await textBox.click();
    await randomDelay(2000, 4000);

    console.log("Typing caption...");
    await page.keyboard.type(caption, { delay: 60 });
    await randomDelay(3000, 5000);

    if (mediaPath) {
      console.log(`Attaching media: ${mediaPath}`);
      const fileInput = await page.waitForSelector('input[type="file"][data-testid="fileInput"]', { timeout: 30000 });
      await fileInput.setInputFiles(mediaPath);
      
      console.log("Waiting for media processing...");
      // Try to wait for the thumbnail or edit button
      try {
          await page.waitForSelector('button[aria-label="Edit media"]', { timeout: 120000 });
          console.log("Media ready.");
      } catch (e) {
          console.log("Media processing indicator not found, but continuing...");
      }
      await randomDelay(8000, 12000);
    }

    console.log("Clicking Post...");
    // Force click via JS if it's tricky
    await page.evaluate(() => {
        const btn = document.querySelector('button[data-testid="tweetButton"]');
        if (btn) btn.click();
    });
    
    console.log("Waiting for confirmation...");
    await randomDelay(5000, 8000);
    await page.screenshot({ path: '/tmp/post_final.png' });
    
    // Check if redirect or text box cleared
    const text = await page.evaluate(() => document.querySelector('div[data-testid="tweetTextarea_0"]')?.innerText || "");
    if (text.length > 5 && page.url().includes('/compose/post')) {
       console.log("Warning: Text box not empty. Attempting direct click via mouse...");
       const btn = await page.waitForSelector('button[data-testid="tweetButton"]');
       await btn.click({ force: true });
       await randomDelay(5000, 8000);
    }
    
    console.log("✅ Post process completed.");

  } catch (e) {
    console.error("❌ Failed:", e.message);
    await page.screenshot({ path: '/tmp/post_error.png' });
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
