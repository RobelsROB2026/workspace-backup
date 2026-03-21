---
name: x-poster
description: 'Post text and media to X (Twitter) using headful browser automation to avoid bot detection. Use when you need to post a tweet (with or without video/image media) to the @barryhauler account or any logged-in X account. This uses stealth Playwright in non-headless mode with natural human typing and delays.'
metadata:
  {
    "openclaw": { "emoji": "🐦", "requires": { "anyBins": ["node"] } },
  }
---

# X-Poster (Stealth Web UI)

This skill allows OpenClaw to post to X (Twitter) via an automated, headful browser session. Because X aggressively flags headless API wrappers and raw automation (like `twikit`), this method uses `playwright-extra` with the `stealth` plugin, running a visible Chrome instance (`headless: false`) and typing naturally.

## Usage

Use the `exec` tool to run the `x-poster.js` script located in this folder.

```bash
# Basic usage (text only)
node /Users/roba/.openclaw/workspace/skills/x-poster/x-poster.js "This is a test tweet from the stealth poster!"

# With media (video or image)
node /Users/roba/.openclaw/workspace/skills/x-poster/x-poster.js "Check out this awesome video!" /path/to/video.mp4
```

## How it Works

1.  **Stealth Browser:** Launches a visible Chromium instance on the Mac mini.
2.  **Authentication:** Ingests Twikit cookies from `/tmp/openclaw/uploads/twikit_cookies.json` (or you can provide a custom cookie file path).
3.  **Natural Interaction:**
    *   Navigates to `https://x.com/compose/post`
    *   Waits for DOM to load naturally
    *   Types the caption character-by-character with random delays
    *   Uploads media via the DOM file input
    *   Waits for media processing to complete
    *   Clicks the Post button and waits for the success toast.

## Setup Requirements

The project must have `playwright`, `playwright-extra`, and `puppeteer-extra-plugin-stealth` installed. This is currently satisfied by the `~/research/social-auto` node_modules.

To make the script standalone, it links to those global or local modules.

