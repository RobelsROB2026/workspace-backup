const { chromium } = require('playwright');
(async () => {
  console.log('Connecting via CDP...');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  const page = contexts[0].pages()[0];
  
  console.log('Clicking button to open dialog natively...');
  // Force a native click
  const box = await page.locator('div[aria-label="Add photos or video"]').first().boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  
  console.log('Done triggering click.');
  await browser.close();
})();
