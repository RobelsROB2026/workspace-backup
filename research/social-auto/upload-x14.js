const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launchPersistentContext(
    '/Users/roba/.openclaw/browser/profiles/openclaw',
    { headless: false }
  );
  
  const pages = browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();
  
  console.log('Navigating to X...');
  await page.goto('https://x.com/home', { waitUntil: 'load' });
  await page.waitForTimeout(5000);
  
  console.log('Typing shortcut to open post box...');
  await page.keyboard.press('n');
  await page.waitForTimeout(3000);

  console.log('Finding hidden file input via JS execution...');
  await page.evaluate(() => {
      const inputs = document.querySelectorAll('input[type="file"]');
      if (inputs.length > 0) {
          // create a global reference
          window.myFileInput = inputs[0];
      }
  });

  const fileInput = await page.$('input[type="file"]');
  if (fileInput) {
      await fileInput.setInputFiles('/tmp/openclaw/uploads/no-trucking-old-men.mp4');
      console.log('File injected!');
  } else {
      console.log('Still no file input found.');
  }

  await page.waitForTimeout(8000); 

  console.log('Typing caption...');
  await page.keyboard.type('Looks like my past is catching up with me. If you see this wrench on the lot, lock your doors and keep rolling. #truckersoftiktok #barryhauler #trucking');
  
  console.log('Waiting for video processing...');
  await page.waitForTimeout(5000); 
  
  console.log('Clicking Post...');
  await page.click('button[data-testid="tweetButton"]');
  
  await page.waitForTimeout(10000);
  console.log('X upload complete.');
  await browser.close();
})();
