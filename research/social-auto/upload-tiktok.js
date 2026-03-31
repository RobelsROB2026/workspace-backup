const { chromium } = require('playwright');
(async () => {
  console.log('Starting TikTok upload...');
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const page = await browser.newPage();
  console.log('Navigating...');
  await page.goto('https://www.tiktok.com/tiktokstudio/upload?from=webapp', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(5000);
  
  console.log('Finding file input...');
  const fileInput = page.locator('input[type="file"]');
  await fileInput.waitFor({ state: 'attached' });
  
  console.log('Setting file...');
  await fileInput.setInputFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  
  console.log('Waiting 20s for upload...');
  await page.waitForTimeout(20000);
  
  console.log('Typing caption...');
  const textbox = page.locator('.public-DraftEditor-content');
  await textbox.click();
  // Clear any existing
  await page.keyboard.press('Meta+A');
  await page.keyboard.press('Backspace');
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  await page.waitForTimeout(5000);
  
  console.log('Clicking post...');
  // Find the Post button
  await page.click('button:has-text("Post")');
  
  console.log('Waiting 20s for completion...');
  await page.waitForTimeout(20000);
  
  console.log('Done!');
  await browser.close();
})();
