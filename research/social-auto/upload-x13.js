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
  
  console.log('Finding ANY file input...');
  const inputs = await page.locator('input[type="file"]').all();
  if (inputs.length > 0) {
      console.log(`Found ${inputs.length} inputs. Uploading to first...`);
      await inputs[0].setInputFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  } else {
      console.log('None found, clicking the media icon via selector...');
      const [fileChooser] = await Promise.all([
          page.waitForEvent('filechooser'),
          page.locator('button[aria-label="Add photos or video"], div[aria-label="Add photos or video"]').first().click({ force: true })
      ]);
      await fileChooser.setFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
  }

  console.log('File injected! Waiting...');
  await page.waitForTimeout(8000); 

  console.log('Typing caption...');
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Waiting for video processing...');
  await page.waitForTimeout(5000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButton"]');
  
  await page.waitForTimeout(10000);
  console.log('X upload complete.');
  await browser.close();
})();
