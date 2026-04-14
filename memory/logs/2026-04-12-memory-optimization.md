# Memory Optimization Changes — 2026-04-12

Robel and Claude Code applied these changes to stabilize the gateway on this 8GB Mac Mini.
These are **intentional** — do NOT revert them.

## Problem
Gateway was crashing repeatedly from macOS memory pressure (SIGTERM).
Root causes:
1. Cron jobs with `wakeMode: "now"` re-fired on every restart, causing crash loops
2. 4 concurrent agents + 8 subagents too much for 8GB RAM
3. Browser plugin spawning Chrome (200-500MB per profile) during cron jobs
4. Heartbeats loading full context across all agents
5. No Node.js heap limit — gateway grew to 700MB+

## Changes Applied

### openclaw.json
- `maxConcurrent`: 4 → **1** (only one agent active at a time)
- `subagents.maxConcurrent`: 8 → **2**
- `contextTokens`: added, set to **100,000** (down from default 200k)
- `bootstrapMaxChars`: added, set to **10,000** (down from default 20k)
- `bootstrapTotalMaxChars`: added, set to **50,000** (down from default 150k)
- `heartbeat.isolatedSession`: **true** (no longer loads full context)
- `heartbeat.lightContext`: **true** (minimal bootstrap per heartbeat)
- `contextPruning`: enabled with `cache-ttl` mode, 5-min TTL
- `session.maintenance`: enabled with 14-day prune, 500MB disk cap
- `browser` plugin: **disabled** (too memory-hungry for 8GB)
- `ollama` plugin: **disabled** (no local models remain)

### LaunchAgent plist
- Added `NODE_OPTIONS=--max-old-space-size=2048` to cap V8 heap at 2GB

### Cron jobs
- FMCSA Daily Sync: stays at **23:00**, `wakeMode: next-heartbeat`
- Trucking Nationality Tagger: moved to **00:00**, `wakeMode: next-heartbeat`
- Hypnosis NLP Ingest: moved to **01:00**, `wakeMode: next-heartbeat`
- Added "Missed Cron Catch-Up" job at **06:00** (`wakeMode: now`) — lightweight flash job that checks if any daily jobs were missed and re-runs them one at a time

### Removed
- Ollama app and all local models (gemma4:e4b, qwen3.5:4b)
- Gemma agent and topic 1051 routing
- `OLLAMA_KEEP_ALIVE` from .zshrc

## Important Notes
- If browser automation is needed in the future, re-enable with `headless: true` and limit to one profile
- If gateway still crashes, consider reducing `contextTokens` further to 50,000
- The catch-up cron job (ID: 27101751-4754-4f65-9273-4bd76000cc9a) is the ONLY job with `wakeMode: now` — this is intentional
