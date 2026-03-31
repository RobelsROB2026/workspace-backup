const { chromium } = require('playwright');
(async () => {
  console.log('Connecting to running browser via CDP...');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  const page = contexts[0].pages()[0]; // Just grab the first page
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  
  console.log('Clicking media upload...');
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 10000 }),
    page.locator('div[aria-label="Add photos or video"]').first().click({ force: true })
  ]);
  
  console.log('Setting file payload...');
  await fileChooser.setFiles('/tmp/openclaw/uploads/barry-fever.mp4');
  
  console.log('Waiting 30s for local processing...');
  await page.waitForTimeout(30000);
  
  console.log('Typing caption...');
  const tb = page.locator('div[data-testid="tweetTextarea_0"]');
  await tb.fill('Barry fever dream 🚛 #truckersoftiktok #barryhauler #trucking');
  
  await page.waitForTimeout(5000);
  
  console.log('Clicking post...');
  await page.locator('button[data-testid="tweetButton"]').click();
  
  console.log('Waiting 15s for post to hit server...');
  await page.waitForTimeout(15000);
  
  console.log('Done!');
  await browser.close(); // Only disconnects, doesn't close the browser
})();
