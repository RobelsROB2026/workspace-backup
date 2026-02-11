# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Research Library

Location: `~/research/`

When researching a topic:
1. Check if folder exists → build on existing knowledge
2. New topic → create folder with README.md, sources.md, notes/
3. Update `_index.md` with new topics

Structure per topic:
```
[topic-name]/
├── README.md      # Overview + key takeaways
├── sources.md     # Links, references
├── notes/         # Detailed findings
└── assets/        # PDFs, screenshots, files
```

---

## Browser

**Two options:**
1. **OpenClaw managed browser** (profile: openclaw) - isolated, no extension needed
2. **Chrome extension relay** (profile: chrome) - Robel's actual Chrome

**Chrome extension workflow:**
- If relay disconnected → use Peekaboo to click the OpenClaw toolbar icon
- Once connected → use browser tool with `profile=chrome`
- This lets me use Robel's logged-in sessions (X, Gmail, etc.)

---

## Research Workflow

**Default flow for research tasks:**
1. Browser (profile: openclaw) → Google search, navigate sites
2. `web_fetch` → pull content from URLs (when browser is overkill)
3. `gemini --model gemini-3-flash-preview "Summarize: ..."` → synthesize large content (saves Opus tokens)
4. Store in `~/research/[topic]/` → build knowledge base

Use Gemini 3 Flash for bulk text processing. Save Opus for analysis, decisions, and conversation.

**For analyzing search results:** Pipe to Gemini instead of reading myself:
```bash
gemini --model gemini-3-flash-preview "Analyze these search results and extract key findings: [content]"
```

---

## X/Twitter Access

**bird CLI** (installed at /opt/homebrew/bin/bird) ✓ WORKING:
- Uses Chrome cookies (keychain approved 2026-02-04)
- Account: @RobelAlema63562
- Commands: `bird home`, `bird search "query"`, `bird news`, `bird whoami`
- Ignore Safari warnings (using Chrome, not Safari)

**Browser fallbacks:**
- Chrome extension relay (profile: chrome) - for logged-in browsing
- OpenClaw browser (profile: openclaw) - not logged in yet

---

## Reddit Research

Can fetch Reddit JSON without auth:
```bash
# Works with web_fetch
https://www.reddit.com/r/LocalLLaMA/hot/.json
https://www.reddit.com/r/MachineLearning/hot/.json
```

---

## Scheduling & Automation (IMPORTANT)

**⚠️ OpenClaw's internal cron scheduler has a bug** — recurring jobs don't auto-fire.
Use this hybrid approach instead:

### What Works

| Mechanism | Use For | Reliability |
|-----------|---------|-------------|
| **HEARTBEAT.md** | Batched periodic checks (news, email, maintenance) | ✓ Works |
| **launchd + `openclaw cron run`** | Exact-time tasks (2 AM blog writer) | ✓ Works |
| **OpenClaw cron `--at`** | One-shot reminders ("in 20 min") | ✓ Works |
| **OpenClaw cron recurring** | ❌ DON'T USE | Broken |

### Active Launch Agents

```
~/Library/LaunchAgents/
├── com.openclaw.blog-writer.plist      # Daily 2 AM
├── com.openclaw.weekly-improvement.plist # Sunday 3 AM  
├── com.openclaw.update-check.plist     # Monday 9 AM
```

**Manage with:**
```bash
launchctl list | grep openclaw           # See loaded agents
launchctl unload ~/Library/LaunchAgents/com.openclaw.*.plist  # Stop all
launchctl load ~/Library/LaunchAgents/com.openclaw.*.plist    # Start all
```

### When Adding New Scheduled Tasks

1. **Flexible timing, can batch?** → Add to HEARTBEAT.md
2. **Exact time required?** → Create launchd plist + OpenClaw cron job
3. **One-shot reminder?** → Use `openclaw cron add --at "20m" --session main --system-event "..."`

### Creating New launchd Jobs

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.JOBNAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/openclaw</string>
        <string>cron</string>
        <string>run</string>
        <string>JOB-UUID-HERE</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>2</integer>
        <key>Minute</key><integer>0</integer>
        <!-- Optional: Weekday 0=Sun, 1=Mon, etc. -->
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw-JOBNAME.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw-JOBNAME.log</string>
</dict>
</plist>
```

Then: `launchctl load ~/Library/LaunchAgents/com.openclaw.JOBNAME.plist`

---

## Git Workflow

**Projects (RockLikeAgencyBonds, etc.):** Never push directly to main. Always use PRs:

```bash
# Create branch, make changes, push
git checkout -b feature/description
# ... make changes ...
git add . && git commit -m "type: description"
git push -u origin feature/description

# Create PR via gh CLI
gh pr create --title "description" --body "details"
```

Robel reviews and merges.

**My workspace (workspace-backup):** Direct push to main is fine.

---

Add whatever helps you do your job. This is your cheat sheet.
