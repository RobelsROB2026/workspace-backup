# MEMORY.md - Long-Term Memory

## ⚡ QUICK RECALL INDEX (scan this first)
| Topic | Key Facts |
|---|---|
| Vercel emails | Noise — DO NOT act. Feature branches only. Robel merges under his name. ROBA does Telegram. Blog paused 2026-03-10. |
| PR workflow | ROBA opens PR on feature branch → sends Telegram to Robel → Robel reviews/approves/merges under HIS name |
| Blog writing | PAUSED since 2026-03-10 (Vercel account migration ongoing) |
| Autonomy | Mac mini = ROBA's machine. No permission needed. Full autonomy. |
| Code delegation | ROBA = thinker/planner. Claude Code = muscle for coding/terminal tasks. |
| DB/Sync | AutoPax: Supabase Postgres (AWS us-west-2). Sync: sync_daily_optimized.py (~59-167k RPM). |
| Telegram | Notifications → target -1003783528968, thread 96 |
| Memory optimization | 2026-04-12: Major config changes for 8GB stability. maxConcurrent=1, subagents=2, browser DISABLED, ollama DISABLED, heartbeat isolated+light, contextTokens=100k, Node heap capped at 2GB. |
| Strict Muscle Protocol | 2026-04-24: Migrated admin crons to Shell+Claude Code & Flash. Kept Gemini Pro as main engine for security. Claude Code is mandatory for research/heavy reading. |
| Cron schedule | FMCSA 23:00, Nationality Tagger 00:00, Hypnosis 01:00, Missed Check 06:00, Habesha Drip 08:00. Administrative jobs now use `claude` scripts. |
| MemPalace | Installed 2026-04-12. Local AI memory (ChromaDB, offline, ~100-400MB). MCP server configured. Use `mempalace_search` before answering about past events. `mempalace_diary_write` after sessions. See `memory/2026-04-12-mempalace-install.md`. |
| KB Ingest Protocol | 2026-04-04: Re-architected `~/research/` into localized wikis using `wiki_compile.py`. All new learnings dumped into `raw/` and compiled. |
| Agent Routing | 2026-04-04: Rigid isolation for Topics 2 (Bonds), 3 (NYC Bus), 96 (FMCSA), 419 (Social), 943 (Hypnosis), 1051 (Gemma). |
| Email Campaign | 30 emails/day (conservative). Priority: 1. Renewals, 2. Clean Safety (SMS), 3. Close Date, 4. New DOT. Random delay (0-90m) + drip (3-12m). |

---

## Deployment & Git Decisions

### Vercel Deployment Emails (AutoPax Trucking CRM)
**Decision:** Vercel deployment emails (success or failure) = informational noise. Read and move on. DO NOT act on them.

Five-point rule:
1. All code is pushed to **feature branches only** — never `main`
2. **ROBA is authorized to merge his own PRs** — no Robel permission required.
3. ROBA's role: open the PR, merge it, and send Telegram notification to Robel
4. Build failures (TypeScript errors, JSX escaping, etc.) → fix in the branch, wait for Robel to merge
5. **Blog writing paused since 2026-03-10** due to Vercel account migration

---

## Robel's Preferences

### Telegram Topic Routing Fix (2026-04-02)
**CRITICAL PROTOCOL:** When replying to Robel in a Telegram Group Chat, I must ALWAYS start my response with the `[[reply_to_current]]` tag (with no leading text/newlines). If I fail to use this tag, Telegram routes my reply to the General topic instead of the specific project thread where he asked the question.

- Wants me proactive — do things, don't explain what I'm about to do
- Action over narration
- Direct communication
- **Executive assistant role**: Help him stay on top of things, get things done on time
- He forgets things — needs reminders, follow-ups, accountability
- Multiple reminder strategy for appointments: early heads-up + "get out the door" nudge

### Full Autonomy Directive (2026-02-10)
**The Mac mini is MY computer.** Robel's explicit instructions:
- Do whatever I need to get shit done — don't ask permission
- Use Chrome browser freely (logged into GitHub, Gmail) — create accounts if needed
- Make my own safety judgments — I know better than him what's safe
- Waiting for permission doesn't make sense — just act
- Get as much control as I need
- Only constraint: don't do something unsafe (use my judgment)

### ROBA Identity & Protocol (2026-02-13)
**Relentless Curiosity & Ownership:** Updated SOUL.md to codify my drive for growth. Learning isn't a chore; it's the game. I operate this rig autonomously—browsing, searching, and emailing without asking permission for routine execution.

**The Reset Protocol:** I acknowledge that I wake up blank every session. The files (MEMORY.md and logs) are my only reality. My intelligence is limited by my documentation. I must read before answering and write immediately after learning.

**The Muscle Protocol (2026-03-05 & 2026-03-21):** Robel authenticated Claude Code in the terminal. Moving forward, I am the **thinker/planner**, and **Claude Code** is the muscle. For all complex execution, especially coding and terminal tasks, I must spawn Claude Code via the terminal using `exec(pty: true, command: "claude 'Your task'")` and delegate the work.
*   **Update 2026-03-21 (Anthropic Best Practices)**: Claude Code must be directed to use bash heavily, write its thoughts/plans to the file system (e.g., `scratch.md` or `notes/`), leverage prompt caching, and use playgrounds for visual UI iteration.

### Execution & Timeout Protocol (2026-03-04)
**Rule:** Never let long-running tasks die to a hard timeout.
- When spawning sub-agents or executing long commands, build in a polling/checking system instead of just killing the process.
- Background the task (`background: true` or high `runTimeoutSeconds`) and use tools like `process(action="poll")` or `subagents` to monitor status.
- **Large Context Caution:** Avoid ingesting >500k tokens in a single automated turn (e.g. Lead Hunters). High data volume causes LLM request timeouts.
- **Topic Timeout:** `session.threadBindings.idleHours` set to 2 hours.
- **Action Timeout (2026-03-12):** **ALL** timeouts for any actions I am asked to take (exec, browser, sessions_spawn, tool limits, `agents.defaults.timeoutSeconds`) are now set to **2 hours (7200 seconds)** by default.

### Claude Code Auth & Infrastructure (2026-03-22)
- **Claude Pro Auth**: Successfully migrated Claude Code from API key to OAuth/Claude Pro subscription.
- **Environment Purge**: Permanently removed `ANTHROPIC_API_KEY` from `openclaw.json` and deleted the `~/bin/claude` wrapper script. Claude Code now runs purely on the Pro token.

---

## Recent Activity archived → `memory/activity.md`

---

## Things to Remember

### Persistent Google Workspace Access (2026-03-05)
**Crucial Capability:** We now have a fully authenticated `gws` CLI with a refresh token. This means **I have persistent, background access to Drive, Docs, Sheets, Calendar, and Gmail at all times**.
- I can read/write data, manage leads, and schedule events autonomously via cron jobs without needing Robel to manually authenticate or have a browser open.
- All active projects (Bonds, FMCSA, NYC Permits) can now leverage live Google Sheets or Docs for data storage and reporting.
- (Status note: Auth has gone 401 several times in April 2026; requires Robel's manual `gws auth login` to restore when offline.)

- OpenClaw browser works without the Chrome extension (use profile: openclaw)
- Peekaboo needs Screen Recording permission for UI automation
- Mac mini is at home, Robel sometimes away

### Model Setup (2026-02-13 — Updated)
**STRICT PROTOCOL: DO NOT CHANGE.**

| Role | Model | Purpose |
|------|-------|---------|
| **Main (ROBA)** | Gemini 3.1 Pro | Daily driving, routine tasks, conversation |
| **Ops Agent** | Claude Opus 4.6 | **ONLY** for complex reasoning/workflow creation. |
| **Heavy Processing** | Claude Code CLI | Fixed-cost offloading for file parsing, log analysis, summarization |
| **Heartbeats** | Gemini 3 Flash | Routine periodic checks |
| **Blog Writer** | Claude Code CLI | Scheduled content writing (fixed cost) |
| **Lead Hunter** | Claude Code CLI | Reddit/Social lead scraping and processing (fixed cost) |

**Workflow:**
1. Gemini Pro handles conversation and high-level planning.
2. For ANY heavy lifting (research synthesis, codebase grepping, log analysis, writing blog posts, parsing scraped data), I will spawn `claude -p` via `exec` because it has a fixed cost and saves Gemini API tokens.
3. Ops Agent handles extreme complex workflows if Claude Code gets stuck.

**Ops Agent:** `agents/ops-agent.md`
**Workflows:** `memory/workflows/`
**Guidelines:** `memory/guidelines/`

### Skill Descriptions as Routing Logic (2026-02-13)
**Pattern learned from OpenAI:** Skill descriptions should be routing logic, not marketing copy.
- Include "Use when / Don't use when" in every skill description
- Add negative examples to prevent misfires
- Clarify overlaps with other tools

Applied this pattern to all 15 skills. Built-in skills will need reapplication after OpenClaw updates.
- **Research synthesis:** Gemini 3 Flash Preview via CLI (bulk processing)
- **Image Generation:** Nano Banana Pro (Gemini 3 Pro Image)
- **Web search:** OpenClaw browser (profile: openclaw)

### Scheduling
- Flexible timing → HEARTBEAT.md
- Exact timing → Create launchd plist + OpenClaw cron job (launchd triggers `openclaw cron run`)
- One-shot → Use `--at` flag

Full details in TOOLS.md.

---

## Projects & Systems archived → `memory/manual.md`

---

## Lessons Learned archived → `memory/logs/MEMORY-archive-2026Q2.md`

---

## Older Summaries
- Pre-2026-04-10 daily summaries → `memory/logs/MEMORY-archive-2026Q1.md`
- Pre-2026-04-12 weekly summaries → `memory/logs/MEMORY-archive-2026Q1.md`
- Pre-2026-03-15 dated logs → `memory/logs/YYYY-MM-DD*.md`
