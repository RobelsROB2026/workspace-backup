const { chromium } = require('playwright');
(async () => {
  console.log('Connecting via CDP...');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  const page = contexts[0].pages()[0];
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post', { waitUntil: 'load' });
  await page.waitForTimeout(5000);
  
  console.log('Setting file payload...');
  const fileInput = page.locator('input[data-testid="fileInput"]').first();
  await fileInput.setInputFiles('/tmp/openclaw/uploads/barry-fever.mp4');
  
  console.log('Waiting 30s for Twitter to process the video locally...');
  await page.waitForTimeout(30000);
  
  console.log('Checking progress bar...');
  let hasProgress = await page.locator('[role="progressbar"]').count() > 0;
  while (hasProgress) {
      console.log('Still processing...');
      await page.waitForTimeout(5000);
      hasProgress = await page.locator('[role="progressbar"]').count() > 0;
  }
  console.log('Processing complete!');
  
  console.log('Typing caption...');
  const tb = page.locator('div[data-testid="tweetTextarea_0"]');
  await tb.fill('Barry fever dream 🚛 #truckersoftiktok #barryhauler #trucking');
  
  await page.waitForTimeout(3000);
  
  console.log('Clicking post...');
  await page.locator('button[data-testid="tweetButton"]').click();
  
  console.log('Waiting 15s for post to send...');
  await page.waitForTimeout(15000);
  
  console.log('Done!');
  await browser.close();
})();
