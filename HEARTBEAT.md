# HEARTBEAT.md - Periodic Checks

## OpenClaw Ecosystem (1-2x daily)
Check `memory/heartbeat-state.json` for last check times. Look for:

- **ClawHub** (https://clawhub.com) - New skills we could use
- **OpenClaw Discord** - Tips, hacks, community tricks
- **OpenClaw GitHub** - New releases, useful issues/discussions
- Log findings to `memory/openclaw-tips.md`

## AI News Highlights (May 2026)
- **v2026.5.14** is the latest OpenClaw release (fixes Codex refresh errors, preserves tool media, improvements to Copilot Gemini image descriptions).
- **ClawHavoc** malware campaign on ClawHub is distributing info stealers and reverse shells via malicious skills. Security audit found hundreds of malicious skills; use only verified skills.
- **GitHub CVE-2026-3854** patched (RCE via crafted push access). High severity flaw; update local git/gh/GitHub Enterprise.
- **Remy (Google)** and **Hatch (Meta)** AI agents in development; Remy is a proactive 24/7 personal assistant; Hatch is an agentic assistant for shopping/content on Meta platforms.
- **Grok 4.3** released with native video understanding and 1M-2M token context window.
- **OpenClaw Discord** maintains strict "no crypto" policy after $CLAWD scam.

## Weekly Self-Improvement (Friday Night ROBA Optimization Loop)
- **Time:** Friday nights (23:00 - 03:00).
- **Mandate:** Run the `autoresearch-loops/roba-optimization/program.md` suite to evolve ROBA's core `MEMORY.md` and `HEARTBEAT.md` files.
- **Process:** Spawn Claude Code to mutate ROBA's core files, test a sandboxed clone against the benchmark suite, grade the clone's memory/tone/execution, and commit the winning instructions to the live workspace for Monday morning.

## Maintenance (once daily, prefer night)
- Review recent `memory/logs/*.md` files
- Update `MEMORY.md` with significant learnings
- Check git status of workspace, commit if needed

## Memory Hygiene (Gen66, 2026-04-24)
- **Quick Recall Index** at the top of `MEMORY.md` is load-bearing for benchmark Q1. Never delete or reorder rows; only update values in place.
- **Daily/weekly summaries** older than 14 days move to `memory/logs/MEMORY-archive-YYYYqQ.md`. Keep `MEMORY.md` under 400 lines.
- **Dedup rule:** if a section title repeats (e.g., two `New York Permit Breakthrough` entries), merge or archive the older copy — never let duplicates accumulate.
- **Source of truth for older context:** `memory/logs/`. Grep there before claiming something was never recorded.

## Nightly Lead Gen Autoresearch Loop (Mandatory)
- **Time:** Once a night (prefer 23:00 - 03:00).
- **Mandate:** Run an evolutionary, empirical optimization loop on the AutoPax systems, strictly following the Karpathy `autoresearch` methodology.
- **Process:**
  1. Define a quantifiable metric for the night (e.g., "Phone/Email Enrichment Hit Rate per 100 records", or "Records processed per minute").
  2. Spawn Claude Code in the terminal to run an autonomous loop:
     - Hypothesize a code change (e.g., to `sync_daily_optimized.py` or a scraper).
     - Edit the code.
     - Run a fixed-time test batch (e.g., 5 minutes).
     - Evaluate the metric against the baseline.
     - Keep the code if it improved; `git revert` if it failed.
  3. Let Claude repeat this trial-and-error loop overnight.
  4. In the morning, report the final benchmark improvement and the winning code generation.

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
