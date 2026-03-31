const fs = require('fs');
const { chromium } = require('/Users/roba/research/social-auto/node_modules/playwright-extra');
const stealth = require('/Users/roba/research/social-auto/node_modules/puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const cookiesFile = '/tmp/openclaw/uploads/twikit_cookies.json';
  const browser = await chromium.launch({ headless: false, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  
  const rawCookies = JSON.parse(fs.readFileSync(cookiesFile, 'utf8'));
  let cookiesToSet = Array.isArray(rawCookies) ? rawCookies : Object.keys(rawCookies).map(k => ({ name: k, value: String(rawCookies[k]), domain: '.x.com', path: '/' }));
  if (Array.isArray(rawCookies)) {
    const extra = [];
    rawCookies.forEach(c => {
      if (c.domain.includes('twitter.com')) extra.push({...c, domain: '.x.com'});
      if (c.domain.includes('x.com')) extra.push({...c, domain: '.twitter.com'});
    });
    cookiesToSet.push(...extra);
  }
  await context.addCookies(cookiesToSet);

  const page = await context.newPage();
  await page.goto('https://x.com/barryhauler', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(8000);
  
  const posts = await page.$$eval('article', articles => {
      return articles.map(a => {
          const time = a.querySelector('time');
          const href = time ? time.closest('a').href : null;
          return { text: a.innerText, url: href };
      });
  });
  
  for (let p of posts) {
      if (p.text.toLowerCase().includes('ostrich egg')) {
          console.log(p.url);
          process.exit(0);
      }
  }
  console.log("Not found");
  process.exit(1);
})();
