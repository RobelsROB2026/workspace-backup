# YouTube Shorts Automation Protocol (2026-03-14)
**Context:** Automation established for YouTube Shorts matching X posts. Google is highly sensitive to headless automation on Studio pages.

**Mandatory Rules:**
1. **Always use Playwright with `headless: false`.** Do not run invisible scripts.
2. **Stealth plugin required.** Always inject `puppeteer-extra-plugin-stealth` (via `playwright-extra`) to mask automation signatures.
3. **No API uploads.** The YouTube Data API quota restricts uploads heavily without full app review, and throws automated metadata flags. Always use the Studio Web UI upload flow.
4. **Use Mac Mini Profile.** Use the `openclaw` browser profile or a consistent user profile to maintain Google login tokens instead of fresh cookies.js injections to avoid suspicious login activity flags.
