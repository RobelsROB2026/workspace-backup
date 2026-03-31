const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  
  // Need to get cookies from the new auth state
  const cookies = await contexts[0].cookies();
  const twikitCookies = {};
  for (const c of cookies) {
    if (c.domain.includes('twitter.com') || c.domain.includes('x.com')) {
       twikitCookies[c.name] = c.value;
    }
  }
  
  fs.writeFileSync('/tmp/openclaw/uploads/twikit_cookies.json', JSON.stringify(twikitCookies, null, 2));
  console.log('Twikit cookies updated.');
  await browser.disconnect();
})();
