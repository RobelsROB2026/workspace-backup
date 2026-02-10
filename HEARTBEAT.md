# HEARTBEAT.md - Periodic Checks

## News & Research (2-3x daily)
Check `memory/heartbeat-state.json` for last check times. Rotate through these:

- **TechMeme** - If >6h since last check:
  1. Fetch https://www.techmeme.com/
  2. Extract top 5 stories (headline + summary)
  3. Append to `memory/news-digest.md` with timestamp
  4. Flag any AI/LLM breaking news as URGENT

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
