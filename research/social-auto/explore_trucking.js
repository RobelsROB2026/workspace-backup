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
  
  // Go to search for trucker tags, let's just do #truckdriver
  await page.goto('https://x.com/search?q=%23truckdriver&src=typed_query&f=top');
  await page.waitForTimeout(8000);
  
  const tweets = await page.$$('article[data-testid="tweet"]');
  let data = [];
  
  for (let i = 0; i < Math.min(tweets.length, 10); i++) {
    const t = tweets[i];
    try {
      const textEl = await t.$('div[data-testid="tweetText"]');
      const text = textEl ? await textEl.innerText() : "[No Text]";
      data.push({ index: i, text: text.replace(/\n/g, ' ') });
    } catch(e) {}
  }
  
  console.log(JSON.stringify(data, null, 2));
  
  let liked = 0;
  for (let i = 0; i < tweets.length; i++) {
     if (liked >= 2) break;
     try {
       const likeBtn = await tweets[i].$('button[data-testid="like"]');
       if (likeBtn) {
         await likeBtn.click();
         await page.waitForTimeout(2000);
         console.log(`Liked tweet ${i}: ${data[i].text.substring(0, 50)}...`);
         liked++;
       }
     } catch (e) {}
  }

  await browser.close();
})();
