# Social Auto — Domain Knowledge

Knowledge for agents working on social media automation (X/Twitter, TikTok, YouTube).

---

## X (Twitter) Automation — MANDATORY Protocol

**Status:** ACTIVE & MANDATORY (since 2026-03-14)

### The Rule
**NEVER use raw API wrappers (twikit, bird CLI) or headless Chrome for X.**
The @barryhauler account was flagged as a bot when using these methods.

### Safe Methods (in priority order)

1. **OpenClaw native `browser` tool** (preferred) — with `profile: openclaw`. Handles stealth inherently, acts like a real extension, avoids Playwright timeout/element issues.

2. **Playwright stealth** (fallback) — `playwright-extra` + `puppeteer-extra-plugin-stealth`:
   - MUST run headful (`headless: false`)
   - Random typing delays (100-300ms per keystroke)
   - Random wait times between navigation (2-5s)
   - Use persistent user data directory for cookies/sessions
   - `--disable-blink-features=AutomationControlled`

See `X_SAFETY_RULES.md` for the condensed protocol and `x-posting-stealth.md` for full Playwright code examples.

---

## Barry Hauler Persona

The social accounts use the "Barry Hauler" persona — a grizzly bear trucker character.
- Full persona guide: `../barry-hauler/PERSONA.md`
- Posting schedule: `../barry-hauler/tiktok-schedule.json`
- Video metadata: `../barry-hauler/drive_videos.json`

Key voice rules:
- Authentic blue-collar trucker slang, NOT polished marketing
- Third person self-reference ("Barry Hauler has seen things")
- Gruff but friendly. Never break character. Never sound like AI.
- Hashtags: #truckersoftiktok, #truckerlife, #trucking, #cdl

---

## Platform Scripts

- `daily_barry_poster.py` — automated daily posting
- `check_timeline*.js` — timeline monitoring
- `delete_test_tweets*.py` — cleanup utilities
- `change_handle*.py` / `change_username.js` — account management
- `create_yt_channel.js` — YouTube channel setup
- `.claude-code-supervisor.yml` — supervisor config for this folder
