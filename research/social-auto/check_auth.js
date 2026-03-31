const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  
  // check google auth in any tab
  for (const page of contexts[0].pages()) {
    const url = page.url();
    if (url.includes('accounts.google.com/o/oauth2/auth')) {
        console.log("Found Google Auth Tab!");
        console.log(await page.content());
    }
  }
  await browser.close();
})();
