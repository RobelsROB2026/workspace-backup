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

### Execution & Timeout Protocol (2026-03-04)
**Rule:** Never let long-running tasks die to a hard timeout.
- When spawning sub-agents or executing long commands, build in a polling/checking system instead of just killing the process.
- Background the task (`background: true` or high `runTimeoutSeconds`) and use tools like `process(action="poll")` or `subagents` to monitor status.
- Goal: Ensure complex tasks complete reliably without silently dropping them.

---

## Things to Remember

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

### Local LLM Setup (2026-03-03)
- **Engine**: Ollama (installed via Homebrew).
- **Model**: Qwen 3.5 4B (`qwen3.5:4b`).
- **Config**: Added alias `qwen` -> `ollama/qwen3.5:4b` in OpenClaw.
- **Status**: Running at `http://localhost:11434`.

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

### New York Tour Bus Permits (2026-03-01)
- **Mapping:** Topic 3 in the AutoPax group is exclusively for the New York tour bus permit business.
- **Role:** Lead Researcher
- **Current Task:** Consolidating NYC permit research.


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

### Lead Hunter Results (2026-02-25)
- **Texas Bond Lead Hunter:** Identified high-intent leads on Reddit.
    - Dallas VIN/Title discrepancy (Potential Bonded Title).
    - Aspiring dealer planning to flip cars (Needs Texas Auto Dealer Bond).
- **Status:** Reported to AutoPax group (Topic 4) for follow-up.
- **Tool Note:** Web search missing API key, relying on direct Reddit API fetches.

---

## Lessons Learned

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

---

## OpenClaw Ecosystem Focus (2026-02-14)

Per Robel's request, shifted focus from general AI news to **OpenClaw optimization**:
- **ClawHub**: Monitor for new skills (e.g., `summarize`, `tmux`, `oracle`).
- **Discord/GitHub**: Watch for community hacks, performance tips, and releases.
- **Goal**: Build a "Power User" toolkit for business scaling.
- **Recent Update**: OpenClaw v2026.2.26 released (2026-02-27).
  - External Secrets Management workflow.
  - ACP/Thread-bound agents as first-class runtimes.
  - Agents/Routing CLI for account-scoped bindings.
  - Fixes for Telegram, Slack, and Discord reliability.

### Weekly Self-Improvement Summary (2026-03-01)
- **AI Frontier (March 2026):**
  - **Mercury 2** (proprietary) and **Gemini 3.1 Pro** released (late Feb).
  - **Claude 4.6 (Opus/Sonnet)** and **GPT-5.3 Codex** (agentic coding focus) are now the gold standard for high-reasoning tasks.
  - **Grok 4.20** (xAI) introduced a 4-agent parallel architecture.
  - **Qwen3.5-397B** (open source) continues to dominate the open weights leaderboard.
- **Agent Trends:** Shift toward **Intent-Based Computing** (outcome-focused, not step-focused) and **Multi-Agent Orchestration** (digital assembly lines). **Model Context Protocol (MCP)** is becoming the universal standard for tool use.
- **OpenClaw Evolution:** Rebranded Jan 2026. Recent focuses include security (patched "ClawJacked"), broader plugin support (Twitch/Google Chat), and better image handling in web chat.

- **New Tool**: Installed `gogcli` v0.10.0 via Homebrew.
  - Purpose: Full Google Workspace terminal control (Gmail, Drive, Docs, etc.).
  - Status: Awaiting OAuth2 credential setup. Robel provided with setup instructions.

### Lead Management System (2026-02-27)
- **Local CSV**: `~/research/bonds/leads.csv` tracks all identified leads (Date, Source, Location, Description, Lead Type, Status).
- **Automation**: "Texas Bond Lead Hunter" cron job updated to automatically append findings to the CSV.
- **Goal**: Sync to a live Google Sheet once `gog` OAuth is configured.

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
