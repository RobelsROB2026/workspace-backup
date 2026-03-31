const { chromium } = require('playwright');
(async () => {
  console.log('Starting X script...');
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const page = await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  
  console.log('Attaching file via filechooser intercept...');
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.click('div[aria-label="Add photos or video"]')
  ]);
  
  await fileChooser.setFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  
  console.log('Waiting 10s for preview to load...');
  await page.waitForTimeout(10000);
  
  console.log('Typing caption...');
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  await page.waitForTimeout(3000);
  
  console.log('Clicking Post...');
  await page.locator('button[data-testid="tweetButton"]').click();
  
  await page.waitForTimeout(10000);
  console.log('X upload completed.');
  await browser.close();
})();
