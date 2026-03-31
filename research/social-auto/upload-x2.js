const { chromium } = require('playwright');
(async () => {
  console.log('Connecting to browser profile...');
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const page = await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
  
  console.log('Uploading file...');
  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.click('div[aria-label="Add photos or video"]');
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  
  console.log('Typing caption...');
  await page.waitForSelector('div[data-testid="tweetTextarea_0"]', { state: 'visible' });
  await page.fill('div[data-testid="tweetTextarea_0"]', 'Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Waiting for video processing...');
  await page.waitForTimeout(10000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButton"]');
  
  await page.waitForTimeout(5000);
  console.log('X upload complete.');
  await browser.close();
})();
