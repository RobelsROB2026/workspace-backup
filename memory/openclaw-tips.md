# OpenClaw Tips & Tricks

## Underused Skills (52 bundled, we use ~5)

### High-Value Unused Skills

| Skill | What it does | Why we'd want it |
|-------|--------------|------------------|
| **oracle** | Bundle files + prompt → send to GPT-5.2 Pro for deep analysis | "Long think" mode - 10min-1hr deep dives on complex problems |
| **summarize** | Summarize URLs, YouTube, local files | Faster than browser for content extraction |
| **tmux** | Remote-control coding agents in parallel | Run 5 Codex instances at once on different issues |
| **session-logs** | Search past conversations | Find what we discussed last week |
| **himalaya** | CLI email (IMAP/SMTP) | Read/send email from terminal - no browser needed |
| **apple-reminders** | Manage Apple Reminders via CLI | Syncs with iPhone reminders |
| **sonoscli** | Control Sonos speakers | Play music, set volume, group rooms |
| **openhue** | Control Philips Hue lights | Lights on/off, scenes, colors |
| **coding-agent** | Run Codex/Claude Code in background | Parallel coding with PTY support |

### Already Using
- peekaboo (macOS UI automation)
- github (gh CLI)
- weather
- gemini (bulk text processing)
- nano-banana-pro (image gen)

## Power User Patterns

### 1. Parallel Coding Army (tmux + coding-agent)
Run multiple Codex instances fixing different issues:
```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
bash pty:true workdir:/tmp/issue-78 background:true command:"codex --yolo 'Fix issue #78'"
# Repeat for more issues
process action:list  # Monitor all
```

### 2. Deep Analysis Mode (oracle)
For complex problems, bundle context and send to GPT-5.2 Pro:
```bash
oracle --engine browser --model gpt-5.2-pro -p "Analyze this codebase" --file "src/**"
```
Expect 10min-1hr for deep thinking.

### 3. Fast Content Extraction (summarize)
```bash
summarize "https://example.com" --model google/gemini-3-flash-preview
summarize "https://youtu.be/..." --youtube auto --extract-only  # Transcript
```

### 4. Search Past Conversations (session-logs)
```bash
# Find sessions about a topic
rg -l "keyword" ~/.openclaw/agents/main/sessions/*.jsonl

# Extract user messages from a session
jq -r 'select(.message.role == "user") | .message.content[]? | select(.type == "text") | .text' <session>.jsonl
```

## Hooks (Event-Driven Automation)

### Available Hooks
```bash
openclaw hooks list
```

### Useful Bundled Hooks
- **session-memory** - Auto-save context when you /new
- **command-logger** - Audit trail of all commands
- **boot-md** - Run BOOT.md instructions on gateway start

### Enable:
```bash
openclaw hooks enable session-memory
```

## Gmail Integration
Can wire Gmail → Pub/Sub → OpenClaw webhook for instant email notifications:
```bash
openclaw webhooks gmail setup --account your@gmail.com
```
Requires: gcloud, gog CLI, tailscale

## Pro Tips

### 1. Model Routing
- Heavy thinking: Opus
- Routine/bulk: Gemini Flash
- Long-form analysis: oracle → GPT-5.2 Pro

### 2. Auto-Notify on Background Tasks
Add this to any long prompt:
```
When finished, run: openclaw system event --text "Done: [summary]" --mode now
```

### 3. PTY Required for Coding Agents
Always use `pty:true` when running codex/claude/opencode:
```bash
bash pty:true workdir:~/project command:"codex exec 'your task'"
```

### 4. Cost Tracking
```bash
# Session cost
jq -s '[.[] | .message.usage.cost.total // 0] | add' <session>.jsonl

# Daily costs
for f in ~/.openclaw/agents/main/sessions/*.jsonl; do
  date=$(head -1 "$f" | jq -r '.timestamp' | cut -dT -f1)
  cost=$(jq -s '[.[] | .message.usage.cost.total // 0] | add' "$f")
  echo "$date $cost"
done | awk '{a[$1]+=$2} END {for(d in a) print d, "$"a[d]}' | sort -r
```

---
*Last updated: 2026-02-13*

## New Release Highlights (v2026.2.12)

### 🚀 Cron Reliability
Scheduler received major fixes. It no longer skips jobs when timers drift or re-fires duplicates on restart. Safe to move back from launchd to native OpenClaw cron.

### 🧠 Opus 4.6 Support
Native forward-compatibility for Opus 4.6 added.

### 🛡️ Security
- **SSRF Policy**: Hardened URL-based `input_file`/`input_image` handling.
- **Untrusted Web Content**: Browser snapshots and web fetch results are now wrapped as untrusted content to reduce prompt-injection risk.

### 🪵 Log Improvements
Use `openclaw logs --local-time` to see timestamps in your local timezone instead of UTC.
