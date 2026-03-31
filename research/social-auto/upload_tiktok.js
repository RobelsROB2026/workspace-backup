const { chromium } = require('playwright');
(async () => {
  try {
    const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
    const contexts = browser.contexts();
    // find tiktok tab
    let page = null;
    for (const p of contexts[0].pages()) {
      if (p.url().includes('tiktok.com')) {
        page = p;
        break;
      }
    }
    
    if (!page) {
      console.log('No tiktok page found. Creating one...');
      page = await contexts[0].newPage();
      await page.goto('https://www.tiktok.com/creator-center/upload', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(5000);
    }
    
    console.log('Clicking file chooser...');
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.locator('input[type="file"]').evaluate(el => el.click())
    ]);
    
    console.log('Setting file...');
    await fileChooser.setFiles('/tmp/openclaw/uploads/pineapple.mp4');
    
    console.log('Waiting for upload to finish (up to 60s)...');
    // TikTok shows a "Post" button eventually
    await page.waitForSelector('button:has-text("Post")', { timeout: 60000 });
    
    console.log('Filling caption...');
    const caption = "they said Barry couldn't hit a curveball. 50 years of shifting gears gives you one hell of an arm. #truckersoftiktok #trucking #barryhauler";
    
    // TikTok uses a Draft.js editor for captions
    const editor = page.locator('.public-DraftEditor-content');
    await editor.waitFor({ state: 'visible' });
    await editor.fill(caption);
    
    console.log('Wait a sec before posting...');
    await page.waitForTimeout(3000);
    
    console.log('Clicking Post...');
    await page.locator('button:has-text("Post")').nth(1).click(); // sometimes there's a disabled one or multiple
    
    console.log('Waiting for success...');
    await page.waitForTimeout(10000);
    
    console.log('Done!');
    await browser.close();
  } catch (err) {
    console.error(err);
  }
})();
