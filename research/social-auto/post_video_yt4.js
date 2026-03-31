const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs = require('fs');
const path = require('path');

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

  console.log(`Uploading to YouTube Shorts via CDP: ${localPath}`);

  const browser = await chromium.connectOverCDP('http://localhost:18800');
  
  const contexts = browser.contexts();
  const page = contexts[0].pages()[0]; 

  try {
    console.log("Wait for the title/description box");
    const titleBox = await page.waitForSelector('div#textbox-container', { timeout: 60000 });
    await titleBox.click();
    await randomDelay(1000, 2000);
    // Select all and delete default filename
    await page.keyboard.press('Meta+A');
    await page.keyboard.press('Backspace');
    
    // Type out the title
    await page.keyboard.type(shortTitle, { delay: 45 });
    await randomDelay(1500, 3000);
    
    // Description is the second textbox-container
    const textboxes = await page.$$('div#textbox-container');
    if (textboxes.length > 1) {
        await textboxes[1].click();
        await randomDelay(1000, 2000);
        await page.keyboard.type(caption, { delay: 45 });
    }
    
    // "Not made for kids" radio button
    const notKidsRadio = await page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').click();
    await randomDelay(1500, 3000);

    // Next through checks to visibility
    const nextBtn = await page.locator('ytcp-button#next-button').first();
    for (let i = 0; i < 3; i++) {
        await nextBtn.click();
        await randomDelay(2000, 4000);
    }
    
    // Set to Public
    const publicRadio = await page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').click();
    await randomDelay(1500, 3000);

    // Publish
    const publishBtn = await page.locator('ytcp-button#done-button').first();
    await publishBtn.click();
    
    console.log("Publish button clicked. Waiting to complete...");
    await randomDelay(10000, 15000);

    console.log("Successfully posted to YouTube Shorts via CDP attached browser!");

  } catch (e) {
    console.error("Failed to post via CDP:", e);
    await page.screenshot({ path: '/tmp/yt_upload_error.png' });
    process.exit(1);
  } finally {
    // don't close the browser since it's the main openclaw instance
  }
})();
