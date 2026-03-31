const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  
  const twikitCookies = JSON.parse(fs.readFileSync('/tmp/openclaw/uploads/twikit_cookies.json', 'utf8'));
  let cookiesToSet = [];
  for (let domain of ['.x.com', '.twitter.com']) {
    for (let name of Object.keys(twikitCookies)) {
      cookiesToSet.push({
        name,
        value: twikitCookies[name],
        domain: domain,
        path: '/',
        secure: true,
        sameSite: 'Lax'
      });
    }
  }
  
  await context.addCookies(cookiesToSet);
  const page = await context.newPage();
  
  await page.goto('https://x.com/settings/screen_name');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/tmp/username_change_1b.png' });
  
  await browser.close();
})();
