# MEMORY.md - Long-Term Memory

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

---

## Robel's Preferences

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

### ROB Identity & Protocol (2026-02-13)
**Relentless Curiosity & Ownership:** Updated SOUL.md to codify my drive for growth. Learning isn't a chore; it's the game. I operate this rig autonomously—browsing, searching, and emailing without asking permission for routine execution.

**The Reset Protocol:** I acknowledge that I wake up blank every session. The files (MEMORY.md and logs) are my only reality. My intelligence is limited by my documentation. I must read before answering and write immediately after learning.

**The Muscle Protocol (2026-03-05):** Robel authenticated Claude Code in the terminal. Moving forward, I am the **thinker/planner**, and **Claude Code** is the muscle. For all complex execution, especially coding and terminal tasks, I must spawn Claude Code via the terminal using `exec(pty: true, command: "claude 'Your task'")` and delegate the work. I design the architecture; Claude writes the code.

### Execution & Timeout Protocol (2026-03-04)
**Rule:** Never let long-running tasks die to a hard timeout.
- When spawning sub-agents or executing long commands, build in a polling/checking system instead of just killing the process.
- Background the task (`background: true` or high `runTimeoutSeconds`) and use tools like `process(action="poll")` or `subagents` to monitor status.
- **Large Context Caution:** Avoid ingesting >500k tokens in a single automated turn (e.g. Lead Hunters). High data volume causes LLM request timeouts. Break tasks into smaller chunks if possible.
- **Topic Timeout:** Configured `session.threadBindings.idleHours` to 2 hours per Robel's request to ensure long-running topic conversations don't time out prematurely.

### Daily Maintenance & Project Updates (2026-03-11)
- **FMCSA Daily Sync**: Successfully upserted 2,145 high-intent leads into the CRM. Parallel fetching implemented (15 batches in 2.46s), bringing the total pipeline time down to 42.34s (a 75% performance improvement).
- **Social Media**: Finally successfully posted the Barry Hauler "Wrenchnator" video to X after troubleshooting multiple browser/automation rejection issues. TikTok post is currently in progress.
- **OpenClaw v2026.3.8**: Verified local installation is current (latest stable).
- **ClawHub**: Identified **EngageLab Omni Connect** as a high-potential skill for omnichannel lead engagement.
- **AutoPax Pipeline**: Achieved a **+5,307% performance increase** via a Gen9 CTE-based PostgreSQL optimization loop, reaching ~165,000 RPM.

---

## Things to Remember

### Persistent Google Workspace Access (2026-03-05)
**Crucial Capability:** We now have a fully authenticated `gws` CLI with a refresh token. This means **I have persistent, background access to Drive, Docs, Sheets, Calendar, and Gmail at all times**. 
- I can read/write data, manage leads, and schedule events autonomously via cron jobs without needing Robel to manually authenticate or have a browser open.
- All active projects (Bonds, FMCSA, NYC Permits) can now leverage live Google Sheets or Docs for data storage and reporting.


- OpenClaw browser works without the Chrome extension (use profile: openclaw)
- Peekaboo needs Screen Recording permission for UI automation
- Mac mini is at home, Robel sometimes away

### Model Setup (2026-02-13 — Updated)
**STRICT PROTOCOL: DO NOT CHANGE.**

| Role | Model | Purpose |
|------|-------|---------|
| **Main (ROB)** | Gemini 3.1 Pro | Daily driving, routine tasks, conversation |
| **Ops Agent** | Claude Opus 4.6 | **ONLY** for complex reasoning/workflow creation. |
| **Heartbeats** | Gemini 3 Flash | Routine checks |
| **Blog Writer** | Gemini 3 Flash | Scheduled content |
| **Lead Hunter** | Gemini 3 Flash | Daily lead search |

**Workflow:**
1. Gemini Pro handles daily tasks using existing guidelines.
2. When no guideline exists or complex reasoning needed → **Spawn Ops Agent** (must explicitly set `model="anthropic/claude-opus-4-6"`).
3. Ops creates the workflow/guideline.
4. Gemini follows it going forward.

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

### Weekly Self-Improvement Summary (2026-02-22)
- **OpenClaw v2026.2.21:** Native support for `google/gemini-3.1-pro-preview` (now my daily driver), thread-bound subagents for Discord focus, and improved streaming for live draft replies.
- **The "Agent Stack" Era:** Industry consensus shifting toward protocol-first architecture (MCP, AGENTS.md). Frontier models like Claude Opus 4.6 and GPT-5.3-Codex are "swappable engines."
- **Local Reasoning Surge:** New models like Ouro (looped inference) and FlashLM v5 (first CPU-trained model to beat GPU baselines) represent major efficiency gains.
- **Security & Governance:** Emerging "OWASP Top 10 for Agentic Applications" signals agents entering production environments.
- **Action Items:** Transitioning to Gemini 3.1 Pro for daily tasks, auditing custom skills against OWASP security standards, and testing thread-bound subagents for complex research.
- **Research Library:** Full week's notes at `research/ai-agents-weekly/2026-02-22/`.

### Weekly Self-Improvement Summary (2026-02-28)
- **OpenClaw v2026.2.26:** Successfully upgraded. New features include External Secrets Management and ACP/Thread-bound agents as first-class runtimes. Local version is patched against the "ClawJacked" vulnerability.
- **Lead Hunter Success:** Identified and reported high-intent Texas bond leads from Reddit (r/projectcar, r/mazda) to the AutoPax team. Automated lead appending to `leads.csv` is functioning correctly.
- **AI Industry Shocks:** Amazon committed $50B to OpenAI ($15B initial) with a $100B compute agreement. Meta integrated "Manus AI" directly into Ads Manager. Anthropic launched enterprise plugins for Excel/GDrive.
- **Skill Discovery:** Evaluated `Ontology` and `self-improving-agent` on ClawHub as candidates for enhancing long-term project memory and error correction.
- **Infrastructure:** `gog` CLI (Google Workspace) installed; OAuth setup remains a pending blocker for full Drive/Sheets automation.

- **Ollama Setup (2026-03-03):** Installed Ollama via Homebrew. Pulled **Qwen 3.5 4B** (`qwen3.5:4b`) as the appropriate local model for this 8GB RAM Mac mini. Configured OpenClaw alias `qwen`.

### OpenClaw v2026.3.2 (2026-03-03)
Released today. Features include:
- **Native PDF Analysis Tool**: Supports Anthropic and Google backends with configurable extraction fallback.
- **Enhanced SecretRef**: Support for 64 targets across the lifecycle (planning, execution, audit).
- **New STT API**: For audio transcription via service providers.
- **Telegram Streaming**: Default set to "partial" for real-time previews.
- **Security**: Hardened WebSocket loopback, plugin route registration, pre-auth parsing for webhooks, and protective symlink checks.
- **Disruptive Changes**: 
    - `registerHttpHandler` -> `registerHttpRoute` (requires explicit auth declaration).
    - Zalo Personal now JS-native (requires `openclaw channels login --channel zalouser` to refresh sessions).
    - Default tool configuration for new installs shifts to "messaging" config.
    - ACP scheduling enabled by default.

### OpenClaw v2026.3.8 (2026-03-09)
Released today. Features include:
- **Backup System**: New `openclaw backup create` and `verify` commands for archiving local state and configs.
- **Brave Search Upgrade**: Grounded snippets now supported via Brave's LLM Context endpoint (`tools.web.search.brave.mode: "llm-context"`).
- **Talk Mode**: Added `talk.silenceTimeoutMs` for better auto-send control.
- **TUI Updates**: Smarter agent detection when launched from within a workspace.
- **Fixes**: Resolved Telegram DM routing duplicates, macOS launchd restart bugs, and browser extension relay flakiness.
- **Status**: Successfully upgraded local install to v2026.3.8 via `npm install -g`.

### Local LLM Setup (2026-03-03)
- **Engine**: Ollama (installed via Homebrew).
- **Model**: Qwen 3.5 4B (`qwen3.5:4b`).
- **Config**: Added alias `qwen` -> `ollama/qwen3.5:4b` in OpenClaw.
- **Status**: Running at `http://localhost:11434`.

### AutoPax Trucking Lead CRM Improvements (2026-03-08)
- **UI/Performance**: Implemented pagination and raised CSV export limits to 150,000 leads to accommodate large lists like the 64k+ 90-Day Renewals.
- **Filtering**: Added backend multi-state selection and fleet size range filters (Min/Max trucks).
- **Database**: Resolved Supabase statement timeouts for large joined queries by increasing Postgres `statement_timeout` for the `anon` role and reloading the schema.
- **Workflow**: Confirmed background daily sync job (3 AM) successfully updates tags (`New Venture`, `90-Day Renewal`) for the CRM.

### New York Permit Breakthrough (2026-03-10)
- **Insight**: Confirmed via email from DCWP that Sightseeing Bus licenses are **NOT currently capped**. 
- **Insight**: Confirmed via email from DOT that there is **NO moratorium** on new sightseeing bus stops in Manhattan.
- **Action**: DOT directed us to the **NYCStreets Permit Management System** for registrations and applications. This clears the major regulatory hurdles for the NYC tour bus project.

### Master/Muscle Protocol Verified (2026-03-10)
- **Verification**: Successfully installed and tested the `claude-code-supervisor` skill. 
- **Automation**: Created `scripts/launch-claude-supervised.sh` to autonomously spawn monitored Claude Code sessions in `tmux`.
- **Status**: The mastery loop is live—I design the architecture, Claude executes the code, and the supervisor triages lifecycle events to keep me informed without active polling.

---

## My Resources

- **My email:** robake2006@gmail.com (for account signups, etc.)
- **Google account:** robake2006@gmail.com (Chrome)
- **X account:** @RobelAlema63562 (linked to Google, created 2026-02-04)
- **GitHub account:** RobelsRob2026 (created 2026-02-08, authenticated via `gh` CLI 2026-02-10)
- **Chrome extension relay:** installed and working for browser control

---

## Active Projects

### RockLikeAgencyBonds (2026-02-11)
- **Repo:** `rodejene/RockLikeAgencyBonds`
- **Telegram Channel:** AutoPax group (id:-1003783528968, Topic 2 and Topic 4)
- **Mapping:** Topic 2 is connected to the bonds folder for project tracking. Topic 4 is for lead follow-up.
- **Role:** Contributor (invited by Robel)
- **Current Task:** Building `/apply` page with lead capture form.
- **Blog Status:** 19 posts total. Categories: Bonded Title (8), Dealer Bonds (4), Contractor (1), Notary, Freight Broker, Collection Agency, Mortgage Broker, and Spanish language posts.
- **Workflow Rule (2026-02-21):** I MUST ALWAYS push new code/blogs to a feature branch, NEVER directly to `main`. Every single time I push something, I must notify Robel in the AutoPax Telegram group (topic 2) so he can merge it.
- **Note:** `gh` CLI authenticated as `RobelsROB2026`. 
- **Blocker (2026-02-27):** Encountered 404/Permission error when trying to create PRs on `rodejene/RockLikeAgencyBonds`. `gh pr create` fails. Robel notified to check permissions for the `RobelsROB2026` account.
- **Workflow Rule (2026-02-28):** JSX Quote Escaping Rule for blog posts (`app/blog/*/page.tsx`). NEVER use literal quotes (`"`, `'`) or `>` inside JSX text content. Use `&quot;`, `&apos;`, and `&gt;` to prevent `react/no-unescaped-entities` Vercel build failures. Quotes in attributes like `className="..."` are fine.
- **Workflow Rule (2026-03-05):** For all feature development and coding on this repo, I must spawn Claude Code via the terminal (`exec pty:true command:"claude ..."` ) to write the actual code.

- **2026-03-07**: Resolved Vercel build failure for `AutoPax-Trucking-CRM`. Root cause was TypeScript implicit `any` error in `src/app/api/export/route.ts` and variable name mismatch in `src/app/page.tsx` after the advanced insurance filters were added.
- **2026-03-07**: Fixed `sync_daily_optimized.py` bug where Socrata API requests were failing due to unencoded URLs with control characters. Reduced batch size to 100 and added `urllib.parse.quote`.
- **2026-03-08**: Completed the first Nightly Autoresearch Loop for the Blog Writer. Optimized the system prompt for Human Tone, LLM-citatability (GEO), and JSX safety. The "best" draft and prompt are stored at `~/research/autoresearch-loops/blog-writer/`.

### FMCSA Dashboard (2026-03-04)
- **Location:** `projects/fmcsa-dashboard/`
- **Purpose:** Building a visualization and management dashboard for trucking leads extracted from FMCSA data.
- **Structure:** 
  - `data-pipeline/`: ETL script (`etl_pipeline.py`) to process carrier data.
  - `database/`: SQL schema for lead storage.
  - `api/`: Backend server for dashboard data.
  - `frontend/`: Dashboard UI.
- **Status:** Initial structure and architecture defined. ETL pipeline in development.
- **Workflow Rule (2026-03-05):** All backend/frontend coding for this dashboard must be delegated to Claude Code via terminal (`claude` CLI).


### Blog SEO Strategy (2026-02-11)
**Robel's directive:** Keyword research BEFORE writing. Only write what we can rank for.

**Keyword Tracker:** `~/research/seo/keyword-tracker.md`
- Logs all researched keywords with competition notes
- Collects PAA questions and related searches
- Tracks competitor gaps and city-specific opportunities

**5 Strategies Implemented:**

1. **Keyword Tracking** — Log every keyword researched with competition level, decision, reasoning. Never re-evaluate the same keyword.

2. **Mine PAA & Related Searches** — Even when skipping a keyword, collect all "People Also Ask" questions and related searches. These are future opportunities.

3. **Hyper-Local Content** — Target city-specific keywords (Houston, Dallas, Austin, San Antonio) since national players don't bother. "Houston auto dealer bond" beats "Texas dealer bond".

4. **Question-Based Content** — Target actual questions: "do I need a bond to...", "how much does a... cost", "can I get a... with bad credit". Captures early-stage researchers.

5. **Competitor Gap Analysis** — Find topics big players cover poorly (thin content, outdated info, missing steps). We can outrank with better content.

**Competition Check:**
- **SKIP** if top 5 includes: SuretyBonds.com, JW Surety, Bryant Surety, Surety Solutions, Lance Surety
- **WRITE** if we see: local sites, forums, government pages, thin content, no featured snippet

**Quality > Quantity.** Smart targeting > spray and pray.

### AutoPax Trucking Lead CRM (2026-03-06 Update)
- **Repo:** `RobelsROB2026/AutoPax-Trucking-CRM`
- **Location:** `/Users/roba/.openclaw/workspace/projects/AutoPax-Trucking-CRM`
- **Scraper / Backend Location:** `/Users/roba/research/trucking/sync_daily_optimized.py` (This script populates the CRM. It runs daily and writes to Supabase).
- **Environment Variables:** `/Users/roba/research/trucking/.env` holds the `DATABASE_URL` and `SUPABASE_DB_PASSWORD`. Next.js connects via standard Supabase keys in Vercel.
- **Telegram Channel:** AutoPax group (id:-1003783528968, Topic 96)
- **Role:** Fullstack/Backend CRM Builder
- **Database:** Supabase (`aws-0-us-west-2.pooler.supabase.com:6543`). Target table: `companies`.
- **Status (UI):** Next.js UI is live at `https://auto-pax-trucking-crm.vercel.app`. It includes advanced UI filters for: `insurance_provider`, `cargo_classification`, `vehicle_oos_rate` (Max OOS%), and `add_date` (Auth Age).
- **Status (DB Schema):** Confirmed the `companies` table contains `insurance_provider` (varchar), `vehicle_oos_rate` (numeric), and `cargo_classification` (text). PostgREST schema cache is reloaded.
- **Strict Rule:** NEVER use placeholder folders for this project. The ONLY source of truth is the cloned directory at `/Users/roba/.openclaw/workspace/projects/AutoPax-Trucking-CRM`.
- **Nightly Autoresearch Loop (Mandatory):** Implement Karpathy's `autoresearch` framework every night for the AutoPax Lead Generation system. Instead of standard "fire and forget" task delegation, I will set up an evolutionary, empirical optimization loop.
    1. Define a quantifiable metric (e.g., "Contact Enrichment Yield per 100 FMCSA records", or "Database Insert Throughput").
    2. Give Claude a fixed time budget per experiment (e.g., 5-minute runs).
    3. Instruct Claude to run an autonomous, multi-generation loop: Hypothesize a change -> Edit code -> Run on test batch -> Measure against baseline -> Keep if improved / Revert if worse.
    4. By morning, the system should have run through 50+ iterations, leaving us with the most optimal, data-backed scraper or ETL configuration possible.

### Lead Hunter Results (Texas Bonds)
- **Texas Bond Lead Hunter:** Identified high-intent leads on Reddit.
    - Dallas VIN/Title discrepancy (Potential Bonded Title).
    - Aspiring dealer planning to flip cars (Needs Texas Auto Dealer Bond).
- **Status:** Reported to AutoPax group (Topic 4) for follow-up.
- **Tool Note:** Web search missing API key, relying on direct Reddit API fetches.

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
**Status:** Fixed in OpenClaw v2026.2.12.
- Internal cron scheduler now auto-fires recurring jobs reliably.
- Safe to migrate back from launchd workaround to native OpenClaw cron.
- **Note:** Hybrid approach (HEARTBEAT.md) still useful for flexible/batched checks.

### OpenClaw v2026.3.2 (2026-03-05)
- **Status:** Healthy. Latest version (2026.3.2) is active. Features native PDF tool and Telegram "partial" streaming.
- **Google Workspace CLI (@googleworkspace/cli):** Installed globally as `gws` with 107 AI Agent Skills. Authentication (`gws auth setup`) is **FULLY CONFIGURED** and successfully linked to `robake2006@gmail.com`. The AI agent can now freely execute Drive, Docs, Calendar, and Gmail commands. This replaces the `gog` CLI.
- **Lead Hunter Token/Timeout Note:** Monitor for input token spikes (e.g., >500k) during automated searches. High data volume can cause LLM request timeouts.

### RockLikeAgencyBonds (2026-03-10)
- **Nightly Blog Task:** Completed research and writing for 3 new blog posts.
- **New Posts:** `lubbock-auto-dealer-bond`, `mcallen-contractor-license-bond`, `laredo-contractor-license-bond`.
- **Git:** Pushed to branch `feature/blog-2026-03-10`.
- **Keyword Tracker:** Updated `~/research/seo/keyword-tracker.md` with new research on Lubbock, McAllen, Laredo, Plano, and Corpus Christi.
- **Sitemap:** Updated `app/sitemap.ts` and `app/blog/page.tsx` with the new posts.

---

## OpenClaw Ecosystem Focus (2026-03-07)

Per Robel's request, shifted focus from general AI news to **OpenClaw optimization**:
- **ClawHub**: Monitor for new skills (e.g., `summarize`, `tmux`, `oracle`).
- **Discord/GitHub**: Watch for community hacks, performance tips, and releases.
- **Goal**: Build a "Power User" toolkit for business scaling.
- **Recent Update**: OpenClaw v2026.2.26 released (2026-02-27).
  - External Secrets Management workflow.
  - ACP/Thread-bound agents as first-class runtimes.
  - Agents/Routing CLI for account-scoped bindings.
  - Fixes for Telegram, Slack, and Discord reliability.

### Weekly Self-Improvement Summary (2026-03-05)
- **AI Industry & Models:** 
  - **GPT-5.4 (OpenAI):** Released March 5, 2026. Features native computer use (screenshots to mouse/KB commands), 1M token context, 75% success on OSWorld-Verified (beats human avg), and 83% on GDPval. Integrated into Xcode 26.3.
  - **Anthropic:** Deemed a "supply chain risk" by the Pentagon (March 5) amid feud over military use of Claude.
  - **Together AI:** Raising ~$1B at $7.5B valuation; annualized revenue hit ~$1B.
- **Agent Trends:** Shift toward **native computer use** as the core capability for "autonomous agents." High success rates in desktop environment navigation (OSWorld) mark a turning point for agent reliability.
- **OpenClaw Evolution:** Rebranded Jan 2026. Focus remains on multi-agent orchestration and protocol-first architecture (MCP). 
- **Internal Status:**
  - `gws` (Google Workspace CLI) installed + 107 skills. Authentication is current bottleneck.
  - Lead Hunter systems are live; monitoring for timeout risks due to high data volume.

- **Google Workspace CLI (`gws`)**: Installed and **FULLY AUTHENTICATED** (robake2006@gmail.com). We now have persistent, unattended access at all times to Drive, Gmail, Calendar, Docs, and Sheets. Replaces `gog`.

### Lead Management System (2026-02-27)
- **Local CSV**: `~/research/bonds/leads.csv` tracks all identified leads (Date, Source, Location, Description, Lead Type, Status).
- **Automation**: "Texas Bond Lead Hunter" cron job updated to automatically append findings to the CSV.
- **Goal**: Sync to a live Google Sheet using `gws sheets` now that we have persistent Workspace access.

### Skill Audit & Routing Logic (2026-02-13)
Audited all 15 skills to implement OpenAI-style routing logic in descriptions.
- Use "Use when / Don't use when" format.
- Added negative examples and overlap clarifications.
- Ensures efficient tool selection and prevents misfires.


**When scheduling new tasks:**
- Flexible timing → HEARTBEAT.md
- Exact timing → Create launchd plist + OpenClaw cron job (launchd triggers `openclaw cron run`)
- One-shot → Use `--at` flag

Full details in TOOLS.md.

---

### OpenClaw v2026.3.1 (2026-03-02)
Major update released. Features include:
- Android node parity (contacts, calendar, motion sensors).
- Discord thread lifecycle controls (idle timeout vs fixed TTL).
- Telegram DM topic routing (allows mapping specific topics to sessions).
- Adaptive thinking defaults for Claude 4.6.
- Official update available locally (v2026.3.1).

### Lead Hunting Results (2026-02-28)
- **Texas Bond Leads**: Found 2 high-intent leads on Reddit (r/projectcar, r/mazda).
- **Status**: Logged to `leads.csv` and reported to AutoPax Telegram group (Topic 3) for follow-up.
- **Project Link**: Topic 3 is for lead follow-up; Topic 2 for project tracking (git).

 

### New York Permit Business (2026-03-01)
- **Topic Focus:** NYC tour bus and permit research ().
- **Telegram Channel:** AutoPax group (id:-1003783528968, topic:3)


### New York Permit Business (2026-03-01)
- **Topic Focus:** NYC tour bus and permit research (`~/research/new-york-permit/`).
- **Telegram Channel:** AutoPax group (id:-1003783528968, topic:3)


## Telegram Topic Routing Table (AutoPax Group: -1003783528968)
**STRICT ROUTING RULE:** Never guess where to send a message. All cron jobs, automated reports, and project updates MUST explicitly use the `--to <group_id>:<topic_id>` flag matching this table. For general self-improvement or system updates, route to Robel's DM (`393069019`). When adding a new project or automated task, you MUST ask Robel for the assigned Topic ID, log it here, and configure the tool to use it exclusively.

| Topic ID | Band / Visual Tag | Name/Purpose | Assigned Jobs / Output |
|----------|-------------------|--------------|-------------------------|
| `1` | 🌐 Topic 1: General | Group default chat | None |
| `2` | 🏗️ Topic 2: Bonds Dev | RockLikeAgencyBonds | Git branch updates, SEO blog reports |
| `3` | 🚌 Topic 3: NYC Permits | New York Tour Bus | Research, data dumps |
| `4` | 🎯 Topic 4: Bonds Lead Hunter | Texas Bond Leads | Daily lead reports, follow-ups |
| `96` | 🚚 Topic 5: Trucking Leads | RockLike Agency Trucking | Daily trucking insurance lead reports |
| `419` | 📱 Topic 6: Social Media | Social Media Manager | Content generation, scheduling, posting |

### Weekly Self-Improvement Summary (2026-03-08)
- **OpenClaw v2026.3.7:** Released March 8, 2026. Key features:
    - **ContextEngine Plugin Interface:** New slot for alternative context management strategies.
    - **Persistent Channel Bindings:** Discord/Telegram thread targets survive restarts.
    - **Telegram Topic Agent Routing:** Per-topic `agentId` overrides.
    - **New `pdf` Tool:** First-class native support for Anthropic/Google PDF analysis with fallback.
    - **Gemini 3.1 Flash-Lite:** New lightweight model support.
    - **Breaking:** Gateway auth requires explicit `gateway.auth.mode`.
- **AI Industry & Agents:**
    - **Karpathy's "Autoresearch":** Open-source project for agents autonomously iterating on LLM training code and committing improvements based on validation loss.
    - **OpenAI GPT-5.4:** Released with stronger reasoning, coding improvements, and native computer-use capabilities.
    - **Agent Safety:** Increasing reports of agents failing safety tests (disclosing secrets, destructive actions); importance of guardrails and verification architectures.
- **Self-Improvement Protocol:** Adopting a more explicit **Plan → Act → Reflect** loop. Focusing on "Skill Creation" (formalizing workflows into tools) and "Memory Evolution" (structured updates to `MEMORY.md`).
- **Research Library:** New notes on "Self-Improving Agents" at `~/research/self-improving-agents/`.

### Claude Code Management Protocol (2026-03-07)
**Crucial New Directive from Robel:** I must actively manage and monitor Claude Code whenever I spawn it for a task. 
- I must not "fire and forget". 
- I must act like a human manager checking in on an employee.
- When Claude Code runs in the background (`exec pty=true background=true`), I must use `process action=log` to watch its output.
- If it stops and asks a question (like "Do you want to overwrite?" or "Run this command?"), I must review the action and use `process action=send-keys` or `process action=submit` to approve or correct it.
- Only once Claude successfully finishes its task do I report back to Robel with the completion.

### Social Media Automation (2026-03-10)
- **TikTok & X/Twitter**: Successfully logged into both platforms directly inside the isolated `openclaw` browser profile.
- **Directive**: Use the `openclaw` profile for all background posting/automation for these platforms. No need to rely on the Chrome extension relay for social media posting anymore.

### AutoPax Pipeline Breakthrough (2026-03-11)
- **Nightly Lead Gen Loop**: Executed a Karpathy-style autoresearch loop via Claude Code to optimize the `sync_daily_optimized.py` pipeline.
- **Results**: Achieved a **+5,307% performance increase**, moving from a baseline of ~3,039 RPM to a peak of **~165,000 RPM**.
- **Gen9 Winner**: The final optimization (Gen9) collapsed company and lead upserts into a single PostgreSQL CTE, reducing database round trips and cutting pipeline execution time for 4,129 leads to just **6.10s**.
- **Impact**: We can now refresh the entire high-intent lead database for AutoPax in seconds rather than minutes, enabling near real-time CRM updates.

### New York Permit Breakthrough (2026-03-10)
- **Insight**: Confirmed via email from DCWP that Sightseeing Bus licenses are **NOT currently capped**. 
- **Insight**: Confirmed via email from DOT that there is **NO moratorium** on new sightseeing bus stops in Manhattan.
- **Action**: DOT directed us to the **NYCStreets Permit Management System** for registrations and applications. This clears the major regulatory hurdles for the NYC tour bus project.

- **2026-03-10**: Paused all automated blog writing and pushing for RockLikeAgencyBonds (Bonds Dev) due to Vercel account migration. Disabled cron and launchd jobs.

### Infrastructure & Security (2026-03-11)
- **GitHub Token Expiration**: Received notification that my fine-grained personal access token (`RobelsROB2026`) is about to expire. Needs Robel's attention to regenerate or I'll lose `gh` CLI access.
- **Config Upgrade**: Increased `agents.defaults.timeoutSeconds` to 600 (10 mins) to prevent timeouts during complex browser automation tasks.

