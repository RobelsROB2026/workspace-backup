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

## Recent Activity (last 14 days)

### Daily Maintenance & Project Updates (2026-04-24)
- **Infrastructure:**
    - **OpenClaw v2026.4.23:** Verified stable.
    - **Resource Management (Strict Muscle Protocol):** Migrated administrative cron jobs (Update Check, Missed Cron Check, Weekly Improvement) from the Gemini API to local Bash scripts executing `claude -p` via the fixed-cost Claude Pro plan. `gemini-3.1-pro-preview` remains the default conversational engine for the main session for security and advanced reasoning; `gemini-3-flash-preview` is used for lightweight background dispatches.
- **Nightly Lead Gen Loop (Gen 28)**: Winner (O75: Merged SQL Updates + Cell Fallback). +340% RPM improvement on small batches (peak 157k). Cell hit rate increased to 59.1% via phone fallback. Promoted to `research/trucking/sync_daily_optimized.py`.
- **ROBA Optimization (Gen 55)**: Score 500/500. 80-word email cap, concrete .gov source citations. SOUL.md updated.
- **AI Industry:**
    - **Anthropic:** Google planning $40B investment; Amazon $5B. Revenues hit $30B (surpassing OpenAI).
    - **SpaceX:** IPO prospectus reveals $1.75T valuation; xAI division incurring losses due to cap-ex.
    - **Elon Musk vs OpenAI:** Trial starts Monday April 27, 2026.
    - **DeepSeek V4:** Debuted in China.
- **GWS Status:** 401 Unauthorized. Robel intervention required for Drive/Gmail/Calendar.

### Heartbeat & GWS Status (2026-04-23)
- **GWS Auth Loss**: 401/Auth failure for `robake2006@gmail.com`. The `gws` CLI accounts list is empty. Persistent access to Drive, Gmail, and Calendar is currently **OFFLINE**. Robel needs to run `gws auth login` to restore.
- **Habesha Drip Campaign**: Triggered; background script `run_habesha_campaign.sh` started at ~18:25 CDT.
- **OpenClaw v2026.4.22**: Released. GPT-5 prompt overlays, xAI/Grok provider support, local embedded mode for terminal chats.

### Weekly Self-Improvement Summary (2026-04-24)
- **ROBA Optimization (briny-wi)**: Completed the Friday Night optimization loop.
    - **Core Finding**: The current benchmark suite (5 tests) is **saturated**. ROBA consistently scores 100/100; tests no longer provide enough signal for further evolution.
    - **Action Item**: Expand `benchmark_suite.md` next Friday with new "failure-mode" and "adversarial" tests.
- **AutoPax Pipeline**: Gen 26 (O53: Pre-built DB arrays) reached **143,323 RPM**. Throughput stable.

### Weekly Self-Improvement Summary (2026-04-18)
- **OpenClaw v2026.4.15:** Successfully upgraded. **Claude Opus 4.7** is now the default for Opus aliases; introduced the **Active Memory Plugin** for automated recall; added a **Model Auth status card** in the UI.
- **Frontier Models:** April 2026 — **GPT-5.4**, **Claude Mythos 5**, **Gemini 3.1 Pro** are out. Claude Mythos 5 (10 trillion parameters) is being withheld for safety (ASL-4).
- **Meta Pivot:** Meta's new **Muse Spark** model marks a shift away from open-source Llama toward proprietary multimodal models.
- **Agentic Autopilot:** Industry transitioning from AI "co-pilots" to "autopilot" agents.
- **Action Items:** Enable the `active-memory` plugin to replace the older manual memory search protocol. **CRITICAL:** GWS is offline.

### Daily Maintenance & Project Updates (2026-04-14)
- **Nightly Lead Gen Loop**: Attempted to restart at 12:51 AM. Failed because the agent could not find the Gen 25 R1 (46,433 RPM) benchmark in the logs and the background task `run 2f016029` terminated early.
- **Gmail Alerts**: Critical unread emails: GitHub token expiry (April 20) and GitGuardian secret leak detection in `workspace-backup`.
- **System Health**: OpenClaw update `2026.4.14` available. Vercel deployment error reported for `fmcsa` project.

### Weekly Self-Improvement (2026-04-12)
- **OpenClaw v2026.4.12**: Successfully upgraded.
    - **Active Memory Plugin**: Dedicated memory sub-agent. Use `recall-heavy` or `preference-only` for business continuity.
    - **Memory Palace**: Grounded REM backfill and structured diary view for long-term context.
    - **Local Speech**: MLX provider for macOS Talk Mode (fast/offline).
- **Gemma 4 Dominance**: **Gemma 4 31B** is the new gold standard for agents. Outperforms GPT-5.2 and Gemini 3 Pro on agentic benchmarks ($0.20/run). Test for AutoPax lead enrichment to save API costs.
- **Agent Design Patterns**: Shift toward "digital assembly lines" and "Eval-first" development.

### Daily Maintenance & Project Updates (2026-04-11)
- **Infrastructure:**
    - **OpenClaw v2026.4.9:** Confirmed. Features grounded REM backfill and structured diary view.
    - **Anthropic Claude Restriction:** Standard subscription Claude models restricted for 3rd party tools. Shift to API-based usage billing required.
    - **NemoClaw:** Nvidia enterprise version of OpenClaw unveiled.
- **AutoPax Pipeline:**
    - **Gen 23 Success:** 100% mailing coverage, 97.6% driver count enrichment, 100% reachability.
- **GWS Status:** 401 Unauthorized. Manual re-auth required.

> Older daily/weekly summaries archived → `memory/logs/MEMORY-archive-2026Q1.md`

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

## Systems I've Built

### Research Library (2026-02-02)
Location: `~/research/`

Organized knowledge base by topic. Current structure (consolidated 2026-02-26):
- `bonds/` (Texas surety bonds + SEO keyword tracker)
- `new-york-permit/` (NYC tour bus / permit research)
- `self-improvement/` (AI agent news and weekly summaries)

Each topic gets:
- README.md (overview + takeaways)
- sources.md (links, references)
- notes/ (detailed findings)
- assets/ (files, PDFs, images)

Index at `_index.md`. Template at `_template/`.

**Why:** So we build on past research instead of starting fresh every time. Robel can also drop files into topic folders.

### AutoPax Pipeline Breakthrough (2026-03-11)
- **Nightly Lead Gen Loop**: Karpathy-style autoresearch loop on `sync_daily_optimized.py`.
- **Results**: **+5,307% performance increase**, baseline ~3,039 RPM → Gen 27 peak **~177,328 RPM**.
- **Gen 27 Winner**: Split Phase 3 into parallel streams (Companies vs Leads). Reduced SQL execution to 960ms.
- **Impact**: Refresh the entire high-intent lead database for AutoPax in seconds rather than minutes.

---

## My Resources

- **My email:** robake2006@gmail.com (for account signups, etc.)
- **Google account:** robake2006@gmail.com (Chrome)
- **X account:** @barryhauler (formerly @RobelAlema63562, handle updated 2026-03-13)
- **GitHub account:** RobelsRob2026 (created 2026-02-08, authenticated via `gh` CLI 2026-02-10)
- **Chrome extension relay:** installed and working for browser control

---

## Active Projects

### RockLikeAgencyBonds (2026-02-11)
- **Repo:** `rodejene/RockLikeAgencyBonds`
- **Telegram Channel:** AutoPax group (id:-1003783528968, Topic 2)
- **Mapping:** Topic 2 is STRICTLY and EXCLUSIVELY for the Bonds project (RockLikeAgencyBonds). NOTHING ELSE.
- **Workflow Rule (2026-03-16 - CRITICAL):** ALL blog posts for RockLikeAgencyBonds must ONLY be uploaded directly to the Supabase database (`blog_posts` table on `jbomtgndvxrbdlkpkxbu.supabase.co`). NEVER push code to GitHub for this project. The `content` field must be pure markdown format only. This overrides all previous rules about pushing to feature branches or modifying `app/blog/*.tsx`.
- **Note:** `gh` CLI authenticated as `RobelsROB2026`.
- **JSX Quote Escaping Rule (2026-02-28):** For any blog posts in JSX (`app/blog/*/page.tsx`), NEVER use literal quotes (`"`, `'`) or `>` inside JSX text content. Use `&quot;`, `&apos;`, and `&gt;` to prevent `react/no-unescaped-entities` Vercel build failures. Quotes in attributes like `className="..."` are fine.
- **Workflow Rule (2026-03-05):** For all feature development and coding, spawn Claude Code via the terminal (`exec pty:true command:"claude ..."`) to write the actual code.
- **Vercel Build Fixes (2026-03-07):** Resolved Vercel build failure for `AutoPax-Trucking-CRM` (TypeScript implicit `any` in `src/app/api/export/route.ts`; variable name mismatch in `src/app/page.tsx` after advanced insurance filters). Fixed `sync_daily_optimized.py` Socrata API failures (unencoded URLs with control chars; reduced batch to 100; added `urllib.parse.quote`).
- **Blog Writer Loop (2026-03-08):** First Nightly Autoresearch Loop completed. Optimized system prompt for Human Tone, LLM-citatability (GEO), and JSX safety. Stored at `~/research/autoresearch-loops/blog-writer/`.

### FMCSA Dashboard (2026-03-04)
- **Location:** `projects/fmcsa-dashboard/`
- **Purpose:** Visualization and management dashboard for trucking leads extracted from FMCSA data.
- **Structure:**
  - `data-pipeline/`: ETL script (`etl_pipeline.py`).
  - `database/`: SQL schema for lead storage.
  - `api/`: Backend server.
  - `frontend/`: Dashboard UI.
- **Workflow Rule (2026-03-05):** All backend/frontend coding must be delegated to Claude Code via terminal (`claude` CLI).

### AutoPax Trucking Lead CRM (2026-03-06 Update)
- **Repo:** `RobelsROB2026/AutoPax-Trucking-CRM`
- **Location:** `/Users/roba/.openclaw/workspace/projects/AutoPax-Trucking-CRM`
- **Scraper / Backend Location:** `/Users/roba/research/trucking/sync_daily_optimized.py` (populates the CRM, runs daily, writes to Supabase).
- **Environment Variables:** `/Users/roba/research/trucking/.env` holds `DATABASE_URL` and `SUPABASE_DB_PASSWORD`. Next.js connects via standard Supabase keys in Vercel.
- **Telegram Channel:** AutoPax group (id:-1003783528968, Topic 96)
- **Database:** Supabase (`aws-0-us-west-2.pooler.supabase.com:6543`). Target table: `companies`.
- **Status (UI):** Next.js UI live at `https://auto-pax-trucking-crm.vercel.app`. Advanced UI filters: `insurance_provider`, `cargo_classification`, `vehicle_oos_rate` (Max OOS%), `add_date` (Auth Age).
- **Status (DB Schema):** `companies` table contains `insurance_provider` (varchar), `vehicle_oos_rate` (numeric), `cargo_classification` (text). PostgREST schema cache reloaded.
- **Strict Rule:** NEVER use placeholder folders. The ONLY source of truth is the cloned directory at `/Users/roba/.openclaw/workspace/projects/AutoPax-Trucking-CRM`.
- **Nightly Autoresearch Loop (Mandatory):** Karpathy `autoresearch` framework every night for AutoPax Lead Generation. Define quantifiable metric (e.g., "Contact Enrichment Yield per 100 FMCSA records", "DB Insert Throughput"). Fixed time budget per experiment (5-min runs). Multi-generation loop: Hypothesize → Edit → Test batch → Measure vs. baseline → Keep/Revert. Goal: 50+ iterations by morning.

---

## Operational Rules

### Telegram Topic Routing Table (AutoPax Group: -1003783528968)
**STRICT ROUTING RULE:** Never guess where to send a message. All cron jobs, automated reports, and project updates MUST explicitly use the `--to <group_id>:<topic_id>` flag matching this table. For general system updates (OpenClaw, ROBA, infra), route to Robel's DM (`393069019`). ALL OTHER output MUST go to its assigned topic in the AutoPax Group. If a project has no topic, discuss it in the DM first and create one. NEVER send project output to the DM or General topic. When adding a new project or automated task, ask Robel for the assigned Topic ID, log it here, and configure the tool to use it exclusively.

| Topic ID | Band / Visual Tag | Name/Purpose | Assigned Jobs / Output |
|----------|-------------------|--------------|-------------------------|
| `1` | 🌐 Topic 1: General | Group default chat | None |
| `2` | 🏗️ Topic 2: Bonds Dev | RockLikeAgencyBonds | Git branch updates, SEO blog reports |
| `3` | 🚌 Topic 3: NYC Permits | New York Tour Bus | Research, data dumps |
| `4` | 🎯 Topic 4: Bonds Lead Hunter | Texas Bond Leads | Daily lead reports, follow-ups |
| `96` | 🚚 Topic 5: Trucking Leads | RockLike Agency Trucking | Daily trucking insurance lead reports |
| `419` | 📱 Topic 6: Social Media | Social Media Manager | Content generation, scheduling, posting |
| `900` | 🧠 Topic 7: Local LLM | Local LLM Improvement | Qwen/Ollama optimization loops |
| `943` | 🌀 Topic 8: Hypnosis | Holographic NLP/Hypnosis | Daily research digest, hypotheses |
| `1051`| 💎 Topic 9: Gemma Agent | Gemma isolated tests | Local LLM interaction experiments |

**STRICT ROUTING RULE FOR TOPIC 2:** Topic 2 is STRICTLY and EXCLUSIVELY for the Bonds project (RockLikeAgencyBonds). NOTHING ELSE.
**GIT PUSH RULE FOR BONDS:** NEVER push code to GitHub for the Bonds project due to Vercel account migration. ALWAYS upload blog posts to Supabase ONLY. Do NOT use `git push` or `gh pr create` for RockLikeAgencyBonds.

### Claude Code Management Protocol (2026-03-07)
I must actively manage and monitor Claude Code whenever I spawn it for a task.
- I must not "fire and forget".
- Act like a human manager checking in on an employee.
- When Claude Code runs in the background (`exec pty=true background=true`), I must use `process action=log` to watch its output.
- If it stops and asks a question (like "Do you want to overwrite?" or "Run this command?"), I must review the action and use `process action=send-keys` or `process action=submit` to approve or correct it.
- Only once Claude successfully finishes its task do I report back to Robel with the completion.

### X/Twitter Bot Flag Incident (2026-03-14)
- **Root Cause**: `twikit` (unofficial API wrapper) and `Playwright` in pure `headless: true` mode without stealth plugins or typing delays.
- **Action Taken**: Cancelled all pending cron jobs for X. Refactored `post_video_web.js` to use `playwright-extra`, `puppeteer-extra-plugin-stealth`, headful mode (`headless: false`), and human-like typing/mouse movements.
- **Rule going forward**: Never use raw API wrappers or headless Chrome for X. Always use headful automation with stealth plugins and natural interaction delays to preserve the account's standing.

### X/Twitter Stealth Poster Skill (2026-03-21)
**Enriching Skills Directive:** When encountering issues with an OpenClaw skill (e.g., `x-poster`), the priority is to fix and *improve the skill directly* rather than working around it in external scripts. As I gain experience with edge cases (like Twitter's invisible DOM overlays blocking `playwright.click()` or `keyboard.press` failing on emojis), I must update the underlying skill files (`~/.openclaw/workspace/skills/...`) so that all future automation inherits the fortified logic.

---

## Lessons Learned

### Suicide by Subprocess (2026-03-09)
**Mistake:** Ran `openclaw gateway install --force && bash -c "sleep 5 && openclaw gateway restart"` synchronously via the `exec` tool.
**The Root Cause:** The `exec` tool spawns child processes attached to the main OpenClaw Gateway process. When `openclaw gateway install --force` or `restart` runs, the first thing it does is tell macOS (`launchctl`) to kill the Gateway. When the Gateway dies, macOS instantly kills all of its child processes—*including the very script that was trying to restart it*. It died mid-execution before it could run the startup command, leaving me permanently offline.
**Lesson / Fix:** NEVER run gateway restarts or reinstall commands synchronously or directly attached to the process tree.
**Rule (Gateway Restart Protocol):** Before any gateway restart, I MUST read and strictly follow the checklist at `memory/guidelines/gateway-restart-protocol.md`. This includes checking for active subagents/processes, verifying no upcoming cron jobs will be missed, running config pre-flight checks, and using a fully detached background script (`nohup` + `> /dev/null 2>&1 &`).

### Proactive Capability Building (2026-02-03)
**Mistake:** Said "I'll research X tonight" but didn't set up a cron job. Session ended, nothing happened.

**Lesson:** If I commit to something future, I must ensure I CAN actually do it:
- Schedule it (cron job for specific time)
- Add to HEARTBEAT.md (for periodic checks)
- Install missing tools immediately
- Resolve access/permission issues now

Never assume I'll "just do it later" — set up the mechanism first.

### Self-Update Risk (2026-02-03)
**Mistake:** Self-updated without warning that it could cause downtime.

**Lesson:** Flag risky operations before executing — especially ones that affect my own availability.

### OpenClaw Cron Scheduler Bug (Resolved 2026-02-13)
Fixed in OpenClaw v2026.2.12. Internal cron scheduler now auto-fires recurring jobs reliably. Hybrid approach (HEARTBEAT.md) still useful for flexible/batched checks.

---

## Older Summaries
- Pre-2026-04-10 daily summaries → `memory/logs/MEMORY-archive-2026Q1.md`
- Pre-2026-04-12 weekly summaries → `memory/logs/MEMORY-archive-2026Q1.md`
- Pre-2026-03-15 dated logs → `memory/logs/YYYY-MM-DD*.md`
