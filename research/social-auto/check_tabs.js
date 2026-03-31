const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  for (const context of contexts) {
    const pages = context.pages();
    for (const page of pages) {
      console.log('Tab URL:', page.url());
    }
  }
  await browser.close();
})();
