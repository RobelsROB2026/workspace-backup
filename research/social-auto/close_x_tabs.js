const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  const pages = contexts[0].pages();
  for (const page of pages) {
    const url = page.url();
    if (url.includes('x.com/compose/post')) {
      console.log('Closing tab: ' + url);
      await page.close();
    }
  }
  await browser.close();
})();
