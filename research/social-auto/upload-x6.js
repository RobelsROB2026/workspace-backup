const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const pages = browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  
  console.log('Typing caption...');
  const box = page.locator('.public-DraftEditor-content').first();
  await box.waitFor({ state: 'visible', timeout: 10000 });
  await box.click();
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Uploading file...');
  await page.setInputFiles('input[type="file"]', '/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  
  console.log('Waiting for video processing...');
  await page.waitForTimeout(10000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButtonInline"]');
  
  await page.waitForTimeout(5000);
  console.log('X upload complete.');
  await browser.close();
})();
