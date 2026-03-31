const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs = require('fs');
const path = require('path');

const stateFile = path.join(process.env.HOME, 'research/social-auto/barry_video_state.json');
const prepFile = path.join(process.env.HOME, 'research/social-auto/barry_prepped_post.json');
const cookiesFile = '/tmp/openclaw/uploads/twikit_cookies.json';

// Utility to create random delays to seem more human
const randomDelay = (min, max) => new Promise(resolve => setTimeout(resolve, Math.floor(Math.random() * (max - min + 1) + min)));

(async () => {
  if (!fs.existsSync(prepFile)) {
    console.error("No prepped post found.");
    process.exit(1);
  }

  const prepped = JSON.parse(fs.readFileSync(prepFile, 'utf8'));
  const vidId = prepped.id;
  const localPath = prepped.local_path;
  const caption = prepped.caption;

  console.log(`Uploading via Web UI: ${localPath}`);

  // Run in non-headless mode if possible, or headful for better stealth if running on Mac Mini
  // X looks for headless flags. We will use headless: false if we can, but since it's background, we can try headless with stealth first.
  const browser = await chromium.launch({ 
    headless: false, // UI is active on the Mac Mini! This is the #1 way to avoid bot detection.
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  });

  // Load cookies
  const twikitCookies = JSON.parse(fs.readFileSync(cookiesFile, 'utf8'));
  let cookiesToSet = [];
  for (let domain of ['.x.com', '.twitter.com']) {
    for (let name of Object.keys(twikitCookies)) {
      cookiesToSet.push({
        name,
        value: twikitCookies[name],
        domain: domain,
        path: '/',
        secure: true,
        sameSite: 'Lax'
      });
    }
  }
  await context.addCookies(cookiesToSet);

  const page = await context.newPage();
  
  try {
    await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
    await randomDelay(4000, 7000);

    // Type caption slowly like a human
    const textBox = await page.waitForSelector('div[data-testid="tweetTextarea_0"]', { timeout: 15000 });
    await textBox.click();
    await randomDelay(1000, 2000);
    
    // Type out the caption with random key delays
    await page.keyboard.type(caption, { delay: 45 });
    await randomDelay(1500, 3000);

    // Upload file
    const fileInput = await page.$('input[type="file"]');
    await fileInput.setInputFiles(localPath);
    
    console.log("File attached. Waiting for upload to complete...");
    // Wait for the media to be attached and processed.
    await page.waitForSelector('button[aria-label="Edit media"]', { timeout: 120000 });
    console.log("Upload complete.");
    await randomDelay(3000, 5000);

    // Click Post
    const postBtn = await page.waitForSelector('button[data-testid="tweetButton"]', { timeout: 5000 });
    // Simulate natural mouse movement to the button
    const box = await postBtn.boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
    await randomDelay(500, 1000);
    await page.mouse.down();
    await randomDelay(100, 300);
    await page.mouse.up();
    
    console.log("Post button clicked.");

    // Wait for it to send
    await page.waitForSelector('div[data-testid="toast"]', { timeout: 30000 }).catch(() => console.log("No toast found, but proceeding."));
    console.log("Successfully posted to X via Web UI!");

    // Update state
    let state = { posted_drive_ids: [] };
    if (fs.existsSync(stateFile)) {
      state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    }
    if (!state.posted_drive_ids.includes(vidId)) {
      state.posted_drive_ids.push(vidId);
      fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
    }

    // Clean up
    fs.unlinkSync(prepFile);

  } catch (e) {
    console.error("Failed to post via Web UI:", e);
    await page.screenshot({ path: '/tmp/web_upload_error.png' });
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
