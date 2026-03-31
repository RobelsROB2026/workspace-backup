const { chromium } = require('playwright');

(async () => {
  console.log('Connecting to running browser via CDP...');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  const page = contexts[0].pages()[0];
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  
  console.log('Looking for input[type="file"] directly...');
  const fileInput = page.locator('input[data-testid="fileInput"]').first();
  await fileInput.setInputFiles('/tmp/openclaw/uploads/barry-fever.mp4');
  
  console.log('Waiting 15s for local processing...');
  await page.waitForTimeout(15000);
  
  console.log('Typing caption...');
  const tb = page.locator('div[data-testid="tweetTextarea_0"]').first();
  await tb.fill('Barry fever dream 🚛 #truckersoftiktok #barryhauler #trucking');
  
  await page.waitForTimeout(5000);
  
  console.log('Clicking post...');
  await page.locator('button[data-testid="tweetButton"]').first().click();
  
  console.log('Waiting 15s for post to hit server...');
  await page.waitForTimeout(15000);
  
  console.log('Done!');
  await browser.close(); 
})();
