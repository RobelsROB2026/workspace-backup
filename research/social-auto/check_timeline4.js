const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
  const contexts = browser.contexts();
  const page = contexts[0].pages()[0] || await contexts[0].newPage();
  
  await page.goto('https://x.com/search?q=%23trucking&src=typed_query&f=top');
  await page.waitForTimeout(8000);
  
  const tweets = await page.$$('article[data-testid="tweet"]');
  console.log("Found tweets:", tweets.length);
  
  let data = [];
  let liked = 0;
  
  for (let i = 0; i < tweets.length; i++) {
    const t = tweets[i];
    try {
      const textEl = await t.$('div[data-testid="tweetText"]');
      const text = textEl ? await textEl.innerText() : "[No Text]";
      data.push({ index: i, text: text.replace(/\n/g, ' ') });
      
      // Look for the heart icon (like button)
      const likeBtn = await t.$('button[data-testid="like"]');
      // Look for the unlike button to see if we already liked it
      const unlikeBtn = await t.$('button[data-testid="unlike"]');
      
      if (likeBtn && !unlikeBtn && liked < 3 && text.length > 20 && !text.toLowerCase().includes('barryhauler')) {
         await likeBtn.click();
         await page.waitForTimeout(1000);
         console.log(`Liked tweet: ${text.substring(0, 60)}...`);
         liked++;
      }
    } catch(e) {}
  }
  
  // Save findings to memory to learn what people respond to
  fs.writeFileSync('/Users/roba/research/social-auto/recent_trucking_research.json', JSON.stringify(data, null, 2));
  console.log(`Saved ${data.length} tweets for analysis.`);
  
  await browser.disconnect();
})();
