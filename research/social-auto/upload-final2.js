const { chromium } = require('playwright');
(async () => {
  console.log('Starting...');
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const page = await browser.newPage();
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'load', timeout: 60000 });
  
  await page.waitForTimeout(5000);
  
  console.log('Clicking media upload button...');
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 15000 }),
    page.locator('div[aria-label="Add photos or video"]').first().click({ force: true })
  ]);
  
  console.log('Setting file payload...');
  await fileChooser.setFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  
  console.log('Waiting 15s for local processing...');
  await page.waitForTimeout(15000);
  
  console.log('Typing caption...');
  const tb = page.locator('div[data-testid="tweetTextarea_0"]');
  await tb.fill('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  await page.waitForTimeout(5000);
  
  console.log('Clicking post...');
  await page.locator('button[data-testid="tweetButton"]').click();
  
  console.log('Waiting 15s for post to hit server...');
  await page.waitForTimeout(15000);
  
  console.log('Done!');
  await browser.close();
})();
