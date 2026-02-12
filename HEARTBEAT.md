# HEARTBEAT.md - Periodic Checks

## OpenClaw Ecosystem (1-2x daily)
Check `memory/heartbeat-state.json` for last check times. Look for:

- **ClawHub** (https://clawhub.com) - New skills we could use
- **OpenClaw Discord** - Tips, hacks, community tricks
- **OpenClaw GitHub** - New releases, useful issues/discussions
- Log findings to `memory/openclaw-tips.md`

## Maintenance (once daily, prefer night)
- Review recent `memory/logs/*.md` files
- Update `MEMORY.md` with significant learnings
- Check git status of workspace, commit if needed

## Quick Health Check
- Any urgent unread emails? (if gmail configured)
- Calendar events in next 2 hours?
- Any background tasks completed?

## When to Alert Robel
- Important email arrived
- Meeting in <2 hours
- Breaking AI news
- Something urgent from a project

## When to Stay Quiet (HEARTBEAT_OK)
- Late night (23:00-08:00) unless urgent
- Nothing new since last check
- Last check was <30 min ago

---
Track state in `memory/heartbeat-state.json`:
```json
{
  "lastChecks": {
    "techmeme": null,
    "email": null,
    "calendar": null
  }
}
```
