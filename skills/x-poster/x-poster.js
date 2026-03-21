#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(process.env.HOME, 'research/social-auto/node_modules/playwright-extra'));
const stealth = require(path.join(process.env.HOME, 'research/social-auto/node_modules/puppeteer-extra-plugin-stealth'))();
chromium.use(stealth);

// Parse args
const args = process.argv.slice(2);
if (args.length < 1) {
  console.error("Usage: node x-poster.js <caption_text> [optional_media_path] [optional_cookie_json_path]");
  process.exit(1);
}

const caption = args[0];
const mediaPath = args[1] || null;
const cookiesFile = args[2] || '/tmp/openclaw/uploads/twikit_cookies.json';

// Utility to create random delays to seem more human
const randomDelay = (min, max) => new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1) + min)));

(async () => {
  console.log(`Starting Stealth X-Poster...`);
  console.log(`Caption: ${caption}`);
  if (mediaPath) console.log(`Media: ${mediaPath}`);

  // Run in non-headless mode
  const browser = await chromium.launch({ 
    headless: false, 
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  });

  // Load cookies
  if (fs.existsSync(cookiesFile)) {
    console.log(`Loading cookies from ${cookiesFile}`);
    const rawCookies = JSON.parse(fs.readFileSync(cookiesFile, 'utf8'));
    let cookiesToSet = [];
    
    // Check if it's twikit format (object) or playwright format (array)
    if (!Array.isArray(rawCookies)) {
      for (let domain of ['.x.com', '.twitter.com']) {
        for (let name of Object.keys(rawCookies)) {
          cookiesToSet.push({
            name,
            value: String(rawCookies[name]),
            domain: domain,
            path: '/',
            secure: true,
            sameSite: 'Lax'
          });
        }
      }
    } else {
      cookiesToSet = rawCookies;
      // Ensure both domains exist
      const extraCookies = [];
      for (let c of cookiesToSet) {
        if (c.domain.includes('twitter.com')) extraCookies.push({...c, domain: '.x.com'});
        if (c.domain.includes('x.com')) extraCookies.push({...c, domain: '.twitter.com'});
      }
      cookiesToSet.push(...extraCookies);
    }
    
    await context.addCookies(cookiesToSet);
  } else {
    console.error(`Cookie file not found at ${cookiesFile}. You must be logged in!`);
  }

  const page = await context.newPage();
  
  try {
    console.log("Navigating to compose page...");
    await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
    await randomDelay(4000, 7000);

    // Click the text box
    const textBox = await page.waitForSelector('div[data-testid="tweetTextarea_0"]', { timeout: 15000 });
    await textBox.click();
    await randomDelay(1000, 2000);
    
    // Type out the caption with random key delays to simulate human typing
    console.log("Typing caption...");
    for (const char of caption) {
        await page.keyboard.press(char);
        await page.waitForTimeout(Math.random() * 50 + 10);
    }
    await randomDelay(1500, 3000);

    // Upload file if provided
    if (mediaPath) {
      if (!fs.existsSync(mediaPath)) {
        console.error(`Media file not found: ${mediaPath}`);
        throw new Error("Media missing");
      }
      console.log(`Attaching media: ${mediaPath}`);
      
      const fileChooserPromise = page.waitForEvent('filechooser');
      await page.click('div[aria-label="Add media"]');
      const fileChooser = await fileChooserPromise;
      await fileChooser.setFiles(mediaPath);
      
      console.log("File attached. Waiting for upload to complete...");
      
      // Wait for the edit media button to appear, indicating upload finished
      try {
          await page.waitForSelector('button[aria-label="Edit media"], div[data-testid="attachments"]', { timeout: 120000 });
          console.log("Media processed.");
      } catch (e) {
          console.log("Could not confirm media upload via Edit Media button, but proceeding...");
      }
      await randomDelay(5000, 8000);
    }

    // Click Post
    console.log("Locating Post button...");
    const postBtn = await page.waitForSelector('button[data-testid="tweetButton"]', { timeout: 10000 });
    
    // Simulate natural mouse movement to the button
    const box = await postBtn.boundingBox();
    if (box) {
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
        await randomDelay(500, 1000);
        await page.mouse.down();
        await randomDelay(100, 300);
        await page.mouse.up();
        console.log("Post button clicked.");
    } else {
        await postBtn.click();
        console.log("Post button clicked (fallback).");
    }

    // Wait for the success toast
    try {
        await page.waitForSelector('div[data-testid="toast"]', { timeout: 20000 });
        console.log("Success toast detected!");
    } catch (e) {
        console.log("No toast found, but proceeding. The post likely succeeded.");
    }
    
    await randomDelay(2000, 4000);
    console.log("Done.");

  } catch (e) {
    console.error("\n❌ Failed to post via Web UI:", e);
    await page.screenshot({ path: '/tmp/x_poster_error.png' });
    console.log("Screenshot saved to /tmp/x_poster_error.png");
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
