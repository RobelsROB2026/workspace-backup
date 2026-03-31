const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const page = await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
  
  console.log('Typing caption...');
  await page.waitForSelector('div[data-testid="tweetTextarea_0"]', { state: 'visible' });
  await page.fill('div[data-testid="tweetTextarea_0"]', 'Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Uploading file via input element directly...');
  // X uses an input type=file, we can just find it and set files
  const fileInputs = await page.$$('input[type="file"]');
  if (fileInputs.length > 0) {
      await fileInputs[0].setInputFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  }
  
  console.log('Waiting for video processing...');
  await page.waitForTimeout(10000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButton"]');
  
  await page.waitForTimeout(5000);
  console.log('X upload complete.');
  await browser.close();
})();
