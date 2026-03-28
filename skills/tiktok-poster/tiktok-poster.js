#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require(path.join(process.env.HOME, 'research/social-auto/node_modules/playwright-extra'));
const stealth = require(path.join(process.env.HOME, 'research/social-auto/node_modules/puppeteer-extra-plugin-stealth'))();
chromium.use(stealth);

const args = process.argv.slice(2);
if (args.length < 1) {
  console.error("Usage: node tiktok-poster.js <caption_text> <media_path> [optional_cookie_json_path] [optional_profile_dir]");
  process.exit(1);
}

const caption = args[0];
const mediaPath = args[1] || null;
const cookiesFile = args[2] || '/tmp/openclaw/uploads/tiktok_cookies.json';
const profileDir = args[3] && args[3] !== "none" ? args[3] : null; 

const randomDelay = (min, max) => new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1) + min)));

(async () => {
  console.log(`Starting Stealth TikTok-Poster...`);
  console.log(`Caption: ${caption}`);
  if (mediaPath) console.log(`Media: ${mediaPath}`);

  let browser, context;

  if (profileDir) {
     console.log(`Using persistent profile: ${profileDir}`);
     browser = await chromium.launchPersistentContext(profileDir, {
       headless: false,
       channel: 'chrome', // Use real Chrome to avoid crash on existing profile
       viewport: { width: 1280, height: 800 },
       userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
       args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
     });
     context = browser;
  } else {
     browser = await chromium.launch({ headless: false, args: ['--no-sandbox', '--disable-blink-features=AutomationControlled'] });
     context = await browser.newContext({
       userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
     });

     if (fs.existsSync(cookiesFile)) {
       console.log(`Loading cookies from ${cookiesFile}`);
       const rawCookies = JSON.parse(fs.readFileSync(cookiesFile, 'utf8'));
       let cookiesToSet = Array.isArray(rawCookies) ? rawCookies : Object.keys(rawCookies).map(k => ({ name: k, value: String(rawCookies[k]), domain: '.tiktok.com', path: '/' }));
       if (Array.isArray(rawCookies)) {
         const extra = [];
         rawCookies.forEach(c => {
           if (c.domain.includes('tiktok.com')) extra.push({...c, domain: '.tiktok.com'});
         });
         cookiesToSet.push(...extra);
       }
       await context.addCookies(cookiesToSet);
     } else {
       console.error(`Cookie file not found at ${cookiesFile}. You will need to login manually or provide a valid profile directory.`);
     }
  }

  const page = profileDir ? context.pages()[0] || await context.newPage() : await context.newPage();
  
  try {
    console.log("Navigating to TikTok upload...");
    await page.goto('https://www.tiktok.com/creator-center/upload', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(5000, 8000);

    // Check if redirected to login
    if (page.url().includes('/login')) {
      console.log("Detected login page. TikTok cookies might be expired or missing.");
      console.log("Please login manually within the next 60 seconds...");
      await page.waitForFunction(() => !window.location.href.includes('/login'), { timeout: 60000 }).catch(() => {});
      if (page.url().includes('/login')) {
         throw new Error("Timeout waiting for manual login. Exiting.");
      }
      console.log("Login successful, proceeding to upload...");
      await page.goto('https://www.tiktok.com/creator-center/upload', { waitUntil: 'domcontentloaded' });
      await randomDelay(5000, 8000);
    }

    // TikTok upload sometimes lives in an iframe
    let targetFrame = page;
    const iframes = page.frames();
    for (const frame of iframes) {
      if (frame.url().includes('creator-center')) {
        targetFrame = frame;
        break;
      }
    }

    if (mediaPath) {
      console.log(`Attaching media: ${mediaPath}`);
      const fileInput = await targetFrame.waitForSelector('input[type="file"][accept*="video"]', { timeout: 30000 });
      await fileInput.setInputFiles(mediaPath);
      
      console.log("Waiting for video upload to process...");
      await targetFrame.waitForSelector('.public-DraftEditor-content, div[contenteditable="true"]', { timeout: 120000 });
      console.log("Video uploaded and editor ready.");
      await randomDelay(3000, 5000);
    }

    console.log("Typing caption...");
    const editor = await targetFrame.waitForSelector('.public-DraftEditor-content, div[contenteditable="true"]', { timeout: 15000 });
    await editor.click();
    await randomDelay(1000, 2000);
    
    await page.keyboard.press('Meta+A');
    await page.keyboard.press('Backspace');
    await randomDelay(500, 1000);
    
    await page.keyboard.type(caption, { delay: 50 });
    await randomDelay(2000, 4000);

    console.log("Locating Post button...");
    const postBtns = await targetFrame.$$('button');
    let postBtn = null;
    for (const btn of postBtns) {
        const text = await btn.evaluate(el => el.innerText);
        const disabled = await btn.evaluate(el => el.disabled || el.getAttribute('aria-disabled') === 'true');
        if (text && text.toLowerCase().includes('post') && !disabled) {
            postBtn = btn;
            const className = await btn.evaluate(el => el.className);
            if (className.includes('primary') || className.includes('Button')) {
                break;
            }
        }
    }

    if (!postBtn) {
       console.log("Fallback: Trying to find 'Post' button via querySelector...");
       postBtn = await targetFrame.$('button[data-e2e="post-button"]');
    }

    if (postBtn) {
        console.log("Post button found. Clicking...");
        await postBtn.click({ force: true });
    } else {
        throw new Error("Could not find the Post button or it is disabled.");
    }

    console.log("Checking if post succeeded...");
    try {
        await Promise.race([
            page.waitForSelector('div[data-e2e="success-toast"], div:text-matches("Your video has been uploaded", "i")', { timeout: 20000 }),
            page.waitForSelector('div.modal-container:has-text("Manage your posts")', { timeout: 20000 }),
            page.waitForFunction(() => !window.location.href.includes('upload'), { timeout: 20000 })
        ]);
        console.log("TikTok Post confirmed via toast or redirect!");
    } catch (e) {
        console.log("No clear success indicator seen. Taking screenshot to verify.");
        await page.screenshot({ path: '/tmp/tiktok_post_result.png' });
        console.log("Screenshot saved to /tmp/tiktok_post_result.png");
    }

  } catch (e) {
    console.error("❌ Failed to post via Web UI:", e.message);
    await page.screenshot({ path: '/tmp/tiktok_poster_error.png' });
    console.log("Error Screenshot saved to /tmp/tiktok_poster_error.png");
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
})();
