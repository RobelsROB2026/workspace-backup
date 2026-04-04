# X (Twitter) Stealth Posting Protocol

**Date:** 2026-03-14
**Status:** ACTIVE & MANDATORY

## The Problem
Using unauthorized API wrappers (`twikit`, `bird` CLI) or standard headless browser automation (`headless: true`) results in immediate bot-flagging and shadowbanning by X's anti-bot systems.

## The Mandate
**NEVER use raw API wrappers or headless Chrome for X.**

## The Stealth Method
To safely post to X without triggering bot detection, all scripts and automation MUST adhere to the following strict requirements:

1. **Framework:** Use `playwright-extra` combined with `puppeteer-extra-plugin-stealth`.
2. **Execution Mode:** MUST run in headful mode (`headless: false`). Do not hide the browser.
3. **Human Interaction Simulation:**
   - Add random delays between typing strokes (`delay: 100` to `300` ms).
   - Add random wait times between navigation steps and clicks (e.g., `page.waitForTimeout(2000 + Math.random() * 3000)`).
   - Avoid perfectly straight mouse movements or instant snaps if using coordinates.
4. **Profile Management:** Use a persistent user data directory to maintain cookies/sessions so we aren't constantly logging in from scratch. (e.g., OpenClaw's Chrome extension relay or a dedicated Chrome profile directory).

## Example Playwright Stealth Setup (Node.js)

```javascript
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const browser = await chromium.launch({ 
    headless: false, // MANDATORY
    args: ['--disable-blink-features=AutomationControlled']
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 },
  });

  const page = await context.newPage();
  
  // Natural navigation and typing
  await page.goto('https://x.com/compose/post', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000 + Math.random() * 2000);
  
  // ... interaction logic with typing delays ...
})();
```

## Enforcement
Any agent or script attempting to interact with X must read and implement this protocol before execution.