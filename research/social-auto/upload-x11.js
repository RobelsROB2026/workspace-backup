const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const pages = browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/compose/post');
  await page.waitForTimeout(5000);
  
  console.log('Injecting file into input...');
  const fileInput = await page.$('input[type="file"]');
  if (fileInput) {
      await fileInput.setInputFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
      console.log('File set via setInputFiles.');
  } else {
      console.log('No file input found!');
      await browser.close();
      return;
  }
  
  console.log('File set. Waiting for processing...');
  await page.waitForTimeout(8000); 

  console.log('Typing caption...');
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Waiting before post...');
  await page.waitForTimeout(5000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButton"]');
  
  await page.waitForTimeout(8000);
  console.log('X upload complete.');
  await browser.close();
})();
