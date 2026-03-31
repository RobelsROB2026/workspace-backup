const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  try {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const contexts = browser.contexts();
    
    const cookies = await contexts[0].cookies();
    const tiktokCookies = {};
    for (const c of cookies) {
      if (c.domain.includes('tiktok.com')) {
         tiktokCookies[c.name] = c.value;
      }
    }
    
    fs.mkdirSync('/tmp/openclaw/uploads', { recursive: true });
    fs.writeFileSync('/tmp/openclaw/uploads/tiktok_cookies.json', JSON.stringify(tiktokCookies, null, 2));
    console.log('TikTok Cookies saved. Found: ' + Object.keys(tiktokCookies).length);
    await browser.close();
  } catch (e) {
    console.error(e);
  }
})();
