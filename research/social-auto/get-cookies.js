const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  try {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const contexts = browser.contexts();
    const page = contexts[0].pages()[0];
    
    // go to X to ensure we have the right domain cookies, though they might already be present
    const cookies = await contexts[0].cookies();
    
    // twikit expects a specific format or we can just parse it
    // twikit load_cookies expects a dict of name:value pairs
    const twikitCookies = {};
    for (const c of cookies) {
      if (c.domain.includes('twitter.com') || c.domain.includes('x.com')) {
         twikitCookies[c.name] = c.value;
      }
    }
    
    fs.writeFileSync('/tmp/openclaw/uploads/twikit_cookies.json', JSON.stringify(twikitCookies, null, 2));
    console.log('Cookies saved. Found: ' + Object.keys(twikitCookies).length);
    console.log('Keys: ' + Object.keys(twikitCookies).join(', '));
    await browser.close();
  } catch (e) {
    console.error(e);
  }
})();
