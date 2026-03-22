#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(process.env.HOME, 'research/social-auto/node_modules/playwright-extra'));
const stealth = require(path.join(process.env.HOME, 'research/social-auto/node_modules/puppeteer-extra-plugin-stealth'))();
chromium.use(stealth);

const args = process.argv.slice(2);
const caption = args[0];
const mediaPath = args[1] || null;
const cookiesFile = args[2] || '/tmp/openclaw/uploads/twikit_cookies.json';
const randomDelay = (min, max) => new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1) + min)));

(async () => {
  const browser = await chromium.launch({ headless: false, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  });

  if (fs.existsSync(cookiesFile)) {
    const rawCookies = JSON.parse(fs.readFileSync(cookiesFile, 'utf8'));
    let cookiesToSet = Array.isArray(rawCookies) ? rawCookies : Object.keys(rawCookies).map(k => ({ name: k, value: String(rawCookies[k]), domain: '.x.com', path: '/' }));
    if (Array.isArray(rawCookies)) {
      const extra = [];
      rawCookies.forEach(c => {
        if (c.domain.includes('twitter.com')) extra.push({...c, domain: '.x.com'});
        if (c.domain.includes('x.com')) extra.push({...c, domain: '.twitter.com'});
      });
      cookiesToSet.push(...extra);
    }
    await context.addCookies(cookiesToSet);
  }

  const page = await context.newPage();
  
  try {
    console.log("Navigating...");
    await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
    await randomDelay(4000, 7000);

    const textBox = await page.waitForSelector('div[data-testid="tweetTextarea_0"]', { timeout: 15000 });
    await textBox.click({ force: true });
    await randomDelay(1000, 2000);
    
    console.log("Typing caption...");
    await page.keyboard.type(caption, { delay: 50 });
    await randomDelay(1500, 3000);

    if (mediaPath) {
      console.log(`Attaching media: ${mediaPath}`);
      const fileInput = await page.waitForSelector('input[type="file"][data-testid="fileInput"]', { timeout: 15000 });
      await fileInput.setInputFiles(mediaPath);
      
      console.log("Waiting for media to upload...");
      try {
          await page.waitForSelector('button[aria-label="Edit media"]', { timeout: 60000 });
          console.log("Media processed.");
      } catch (e) {
          console.log("Edit Media button not seen, continuing...");
      }
      await randomDelay(5000, 8000);
    }

    console.log("Waiting for post button to be enabled...");
    await page.waitForSelector('button[data-testid="tweetButton"]:not([disabled])', { timeout: 120000 });
    await randomDelay(1000, 2000);
    
    console.log("Submitting post via DOM click...");
    await page.evaluate(() => {
        const btn = document.querySelector('button[data-testid="tweetButton"]');
        if (btn) btn.click();
    });

    console.log("Checking if post succeeded...");
    // Check for success: wait for the toast OR wait for URL to not be /compose/post
    try {
        await Promise.race([
            page.waitForSelector('div[data-testid="toast"]', { timeout: 15000 }),
            page.waitForFunction(() => window.location.pathname !== '/compose/post', { timeout: 15000 })
        ]);
        console.log("Post confirmed via redirect or toast!");
    } catch (e) {
        console.log("No toast or redirect seen, checking if text box cleared...");
        const text = await page.evaluate(() => document.querySelector('div[data-testid="tweetTextarea_0"]')?.innerText || "");
        if (text.length > 5) {
             throw new Error("Text is still in the compose box and we didn't redirect. Post failed.");
        } else {
             console.log("Text box is empty. Post probably succeeded.");
        }
    }

  } catch (e) {
    console.error("❌ Failed:", e.message);
    const text = await page.evaluate(() => document.body.innerText).catch(()=>"");
    console.error("Page Text:", text.substring(0, 500));
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
