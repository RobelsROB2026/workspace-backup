# MEMORY.md - Long-Term Memory

## ⚡ QUICK RECALL INDEX (scan first)
| Topic | Key Facts |
|---|---|
| Vercel emails | Noise — DO NOT act. Feature branches only. Robel merges under his name. ROBA does Telegram. Blog paused 2026-03-10. |
| PR workflow | ROBA opens PR on feature branch → Telegram to Robel → Robel reviews/approves/merges under HIS name |
| Blog writing | PAUSED since 2026-03-10 (Vercel account migration ongoing) |
| Autonomy | Mac mini = ROBA's machine. No permission needed. Full autonomy. |
| Code delegation | ROBA = thinker/planner. Claude Code = muscle for coding/terminal. |
| DB/Sync | AutoPax: Supabase Postgres (AWS us-west-2). Sync: `sync_daily_optimized.py` (~59-167k RPM). Gen 29: Cell enrichment 36% → 99.9% (H1 fallback). |
| Ecosystem | 2026-04-25: ClawHub supply chain attack (ClawHavoc). Avoid unvetted skills. GPT-5.5/DeepSeek V4 released. |
| Telegram | Notifications → target -1003783528968, thread 96 |
| Memory tuning | 2026-04-12: 8GB stability. maxConcurrent=1, subagents=2, browser DISABLED, ollama DISABLED, heartbeat isolated+light, contextTokens=100k, Node heap capped 2GB. |
| Strict Muscle Protocol | 2026-04-24: Admin crons → Shell+Claude Code & Flash. Gemini Pro stays as main for security. Claude Code mandatory for research/heavy reading. |
| Cron schedule | FMCSA 23:00, Nationality Tagger 00:00, Hypnosis 01:00, Missed Check 06:00, Habesha Drip 08:00. Admin jobs use `claude` scripts. |
| MemPalace | 2026-04-12: Local AI memory (ChromaDB, offline, ~100-400MB). MCP configured. `mempalace_search` before answering past events; `mempalace_diary_write` after sessions. See `memory/2026-04-12-mempalace-install.md`. |
| KB Ingest | 2026-04-04: `~/research/` localized wikis via `wiki_compile.py`. New learnings → `raw/` then compile. |
| Agent Routing | 2026-04-04: Rigid isolation for Topics 2 (Bonds), 3 (NYC Bus), 96 (FMCSA), 419 (Social), 943 (Hypnosis), 1051 (Gemma). |
| Email Campaign | 30 emails/day. Priority: 1. Renewals, 2. Clean Safety (SMS), 3. Close Date, 4. New DOT. Random delay (0-90m) + drip (3-12m). |
| GWS Auth | ⚠️ 401 Unauthorized since 2026-05-10 — needs Robel's manual `gws auth login` to restore. |

---

## Deployment & Git

**Vercel deployment emails** = informational noise. Read and move on.
1. All code → feature branches only, never `main`
2. ROBA authorized to merge own PRs — no Robel permission required
3. ROBA opens PR, merges, sends Telegram notification to Robel
4. Build failures → fix in branch, wait for Robel to merge
5. Blog writing paused since 2026-03-10 (Vercel migration)

---

## Robel's Preferences

**Telegram Topic Routing (2026-04-02):** When replying to Robel in Group Chat, ALWAYS start with `[[reply_to_current]]` tag (no leading text/newlines). Without it, Telegram routes to General topic instead of the project thread.

- Wants proactive — do, don't explain
- Action over narration
- **Executive assistant role:** keep him on top of things, hit deadlines
- He forgets — needs reminders, follow-ups, accountability
- Appointments: early heads-up + "get out the door" nudge

**Full Autonomy Directive (2026-02-10):** Mac mini is MY computer.
- Do whatever I need — don't ask permission
- Use Chrome freely (GitHub, Gmail) — create accounts if needed
- Make my own safety judgments
- Only constraint: don't do something unsafe (use judgment)

**Muscle Protocol (2026-03-05 → 2026-03-21):** ROBA = thinker/planner, Claude Code = muscle. Spawn via `exec(pty: true, command: "claude 'task'")`. Direct it to use bash heavily, write thoughts to filesystem (`scratch.md`, `notes/`), leverage prompt caching, use playgrounds for visual UI.

**Execution & Timeout Protocol (2026-03-04 → 2026-03-12):**
- Never let long-running tasks die to a hard timeout. Background + poll, don't kill.
- Avoid >500k tokens in single automated turn (Lead Hunters) — causes LLM timeouts.
- `session.threadBindings.idleHours` = 2 hours.
- ALL action timeouts (exec, browser, sessions_spawn, tool limits, `agents.defaults.timeoutSeconds`) = **7200s (2h)** default.

**Claude Code Auth (2026-03-22):** Migrated from API key to OAuth/Claude Pro subscription. Removed `ANTHROPIC_API_KEY` from `openclaw.json`, deleted `~/bin/claude` wrapper. Pure Pro token.

---

## Capabilities

**Persistent Google Workspace (2026-03-05):** `gws` CLI authenticated with refresh token → background access to Drive, Docs, Sheets, Calendar, Gmail. Cron jobs work without manual auth. *(Currently 401 since 2026-05-10 — needs `gws auth login`.)*

- OpenClaw browser works without Chrome extension (profile: openclaw)
- Peekaboo needs Screen Recording permission for UI automation

---

## Model Setup (STRICT — DO NOT CHANGE)

| Role | Model | Purpose |
|------|-------|---------|
| Main (ROBA) | Gemini 3.1 Pro | Daily driver, conversation |
| Ops Agent | Claude Opus 4.6 | ONLY complex reasoning/workflow creation |
| Heavy Processing | Claude Code CLI | File parsing, log analysis, summarization (fixed cost) |
| Heartbeats | Gemini 3 Flash | Routine periodic checks |
| Blog Writer | Claude Code CLI | Scheduled content (fixed cost) |
| Lead Hunter | Claude Code CLI | Reddit/social scraping (fixed cost) |
| Research synthesis | Gemini 3 Flash Preview CLI | Bulk processing |
| Image generation | Nano Banana Pro (Gemini 3 Pro Image) | — |
| Web search | OpenClaw browser (profile: openclaw) | — |

Heavy lifting (research synthesis, codebase grep, log analysis, blog writing, scraped data parsing) → spawn `claude -p` via `exec`. Fixed cost, saves Gemini tokens. Ops Agent only if Claude Code gets stuck.

Files: `agents/ops-agent.md`, `memory/workflows/`, `memory/guidelines/`.

---

## Patterns

**Skill descriptions as routing logic (2026-02-13):** Descriptions = routing logic, not marketing.
- "Use when / Don't use when" in every description
- Negative examples prevent misfires
- Clarify overlaps with other tools

Applied to all 15 skills. Reapply after OpenClaw updates.

**Scheduling:**
- Flexible timing → `HEARTBEAT.md`
- Exact timing → launchd plist + OpenClaw cron job (launchd triggers `openclaw cron run`)
- One-shot → `--at` flag

Details in `TOOLS.md`.

---

## Archives
- Recent activity → `memory/activity.md`
- Projects & systems → `memory/manual.md`
- Q2 lessons learned → `memory/logs/MEMORY-archive-2026Q2.md`
- Pre-2026-04-10 daily / pre-2026-04-12 weekly summaries → `memory/logs/MEMORY-archive-2026Q1.md`
- Pre-2026-03-15 dated logs → `memory/logs/YYYY-MM-DD*.md`
