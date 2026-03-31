const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const pages = browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'load' });
  await page.waitForTimeout(5000);
  
  console.log('Typing caption...');
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Looking for file upload input hidden in DOM...');
  const fileInput = page.locator('input[type="file"][data-testid="fileInput"]');
  await fileInput.waitFor({ state: 'attached' });
  await fileInput.setInputFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  console.log('File injected!');
  
  console.log('Waiting for video processing...');
  await page.waitForTimeout(8000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButton"]');
  
  await page.waitForTimeout(8000);
  console.log('X upload complete.');
  await browser.close();
})();
