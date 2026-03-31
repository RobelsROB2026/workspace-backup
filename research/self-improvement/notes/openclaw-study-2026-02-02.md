# OpenClaw Self-Study - 2026-02-02

## What I Learned

### 1. GitHub Releases RSS Available
- URL: `https://github.com/openclaw/openclaw/releases.atom`
- Latest version: 2026.2.1 (released Feb 2, 2026)
- Can monitor for updates via cron job

### 2. Skills System
- **Bundled skills**: Come with OpenClaw install
- **Managed skills**: `~/.openclaw/skills` (shared across agents)
- **Workspace skills**: `<workspace>/skills` (per-agent)
- **ClawHub**: https://clawhub.com for community skills

Skills I have but might not be using fully:
- `nano-banana-pro` - Image generation (Gemini 3 Pro)
- `peekaboo` - macOS UI automation (needs Screen Recording permission)
- `github` - GitHub CLI integration
- `apple-notes` - Apple Notes via `memo` CLI
- `weather` - Weather forecasts
- `gemini` - Gemini CLI for one-shot tasks
- `clawhub` - Install new skills on the fly

### 3. Cron vs Heartbeat
**Use Heartbeat when:**
- Multiple checks can batch together
- Need conversational context
- Timing can drift
- Reducing API calls by combining checks

**Use Cron when:**
- Exact timing matters
- Task needs isolation
- Different model for specific task
- One-shot reminders
- Direct channel delivery without main session

### 4. Isolated Sessions
- Run with `sessionTarget: "isolated"` 
- Good for noisy/frequent tasks
- Can specify different model (e.g., use Sonnet for simple cron tasks)
- Results posted to main session as summary

### 5. What Others Are Doing with OpenClaw
From community shoutouts:
- Autonomous code loops from phone
- Email management (unsubscribes, summaries)
- Calendar checks with traffic-aware reminders
- Custom meditations with TTS
- Building websites from phone
- Health/WHOOP integration
- Smart home control
- Proactive background work

---

## Recommendations for Our Setup

### Immediate Actions

1. **Set up OpenClaw update monitoring**
   - Create cron job to check GitHub releases weekly
   - Alert me when new version available

2. **Grant Peekaboo permissions** (when you're at computer)
   - System Settings → Privacy & Security → Screen Recording → Peekaboo
   - This unlocks macOS UI automation

3. **Consider adding heartbeat checks** (optional):
   - Weather (if relevant)
   - Calendar (if connected)
   - Email (if Gmail hooked up)

### Configuration Changes to Discuss

1. **HEARTBEAT.md is empty** - Should we add periodic checks?
   - Currently heartbeats just verify I'm alive
   - Could add: weather, calendar, email checks

2. **No email/calendar integration** - Worth setting up?
   - Gmail webhook available (`/automation/gmail-pubsub`)
   - Would let me proactively alert on important emails

3. **No Claude Code/Codex integration** - For coding projects
   - Can manage Claude Code sessions remotely
   - Could spawn coding tasks while you're away

### What's Working Well

- ✅ Model setup (Opus for chat, Gemini 3 Flash for heartbeats/research)
- ✅ Research workflow (browser + Gemini synthesis)
- ✅ Memory system (MEMORY.md + daily notes)
- ✅ Research library structure

---

## Setting Suggestion: Cron for Updates

Create a weekly job to check for OpenClaw updates:

```bash
openclaw cron add \
  --name "Check OpenClaw Updates" \
  --cron "0 9 * * 1" \
  --tz "America/Chicago" \
  --session isolated \
  --message "Check https://github.com/openclaw/openclaw/releases for new versions. Compare with current installed version. If newer version exists, summarize what's new and notify me." \
  --model "google/gemini-3-flash-preview" \
  --deliver \
  --channel telegram
```

This runs Monday 9am, uses cheap Gemini, and alerts you in Telegram.

---

*Self-study session complete. Awaiting discussion.*
