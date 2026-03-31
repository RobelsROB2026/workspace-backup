const { chromium } = require('playwright');
const fs = require('fs');
const cookiesFile = '/tmp/openclaw/uploads/twikit_cookies.json';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const twikitCookies = JSON.parse(fs.readFileSync(cookiesFile, 'utf8'));
  let cookiesToSet = [];
  for (let domain of ['.x.com', '.twitter.com']) {
    for (let name of Object.keys(twikitCookies)) {
      cookiesToSet.push({ name, value: twikitCookies[name], domain, path: '/', secure: true, sameSite: 'Lax' });
    }
  }
  await context.addCookies(cookiesToSet);

  const page = await context.newPage();
  
  // Go straight to the search page
  await page.goto('https://x.com/search?q=%23trucking&src=typed_query&f=top', { waitUntil: 'networkidle' });
  await page.waitForTimeout(10000);
  
  const tweets = await page.$$('article[data-testid="tweet"]');
  let data = [];
  let liked = 0;
  
  for (let i = 0; i < Math.min(tweets.length, 10); i++) {
    const t = tweets[i];
    try {
      const textEl = await t.$('div[data-testid="tweetText"]');
      const text = textEl ? await textEl.innerText() : "[No Text]";
      data.push({ index: i, text: text.replace(/\n/g, ' ') });
      
      // Look for the heart icon (like button)
      const likeBtn = await t.$('button[data-testid="like"]');
      if (likeBtn && liked < 2 && text.length > 10 && !text.includes('barryhauler')) {
         await likeBtn.click();
         await page.waitForTimeout(1000);
         console.log(`Liked tweet: ${text.substring(0, 50)}...`);
         liked++;
      }
    } catch(e) {}
  }
  
  console.log("Raw tweets found:");
  console.log(data);
  await browser.close();
})();
