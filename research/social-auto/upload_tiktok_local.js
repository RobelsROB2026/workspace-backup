const { chromium } = require('playwright');
(async () => {
  try {
    const browserContext = await chromium.launchPersistentContext(
      '/Users/roba/.openclaw/browser/openclaw/user-data',
      { 
        headless: false,
        channel: 'chrome',
        args: ['--remote-debugging-port=18800']
      }
    );
    
    // Find or create tiktok tab
    let page = browserContext.pages().find(p => p.url().includes('tiktok.com'));
    if (!page) {
      console.log('No tiktok page found. Creating one...');
      page = await browserContext.newPage();
    }
    
    console.log('Navigating...');
    await page.goto('https://www.tiktok.com/creator-center/upload', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(5000);
    
    console.log('Switching to iframe (if any)...');
    // sometimes tiktok upload is in an iframe
    const frames = page.frames();
    const frame = frames.find(f => f.url().includes('creator-center/upload')) || page;
    
    console.log('Clicking file chooser...');
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      frame.locator('input[type="file"]').evaluate(el => el.click())
    ]);
    
    console.log('Setting file...');
    await fileChooser.setFiles('/tmp/openclaw/uploads/pineapple.mp4');
    
    console.log('Waiting for upload to finish (up to 120s)...');
    // TikTok shows a "Post" button eventually
    await frame.waitForSelector('button:has-text("Post")', { timeout: 120000 });
    
    console.log('Filling caption...');
    const caption = "they said Barry couldn't hit a curveball. 50 years of shifting gears gives you one hell of an arm. #truckersoftiktok #trucking #barryhauler";
    
    // TikTok uses a Draft.js editor for captions
    const editor = frame.locator('.public-DraftEditor-content');
    await editor.waitFor({ state: 'visible' });
    await editor.fill(caption);
    
    console.log('Wait a sec before posting...');
    await page.waitForTimeout(3000);
    
    console.log('Clicking Post...');
    await frame.locator('button:has-text("Post")').nth(1).click({ force: true }).catch(async () => {
        // try without nth if it fails
        await frame.locator('button:has-text("Post")').click({ force: true });
    });
    
    console.log('Waiting for success...');
    await page.waitForTimeout(10000);
    
    console.log('Done!');
    await browserContext.close();
  } catch (err) {
    console.error(err);
  }
})();
