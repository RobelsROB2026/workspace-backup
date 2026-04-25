# MEMORY.md Archive — 2026 Q1 (pre-2026-04-10)

Archived 2026-04-24 as part of Gen66 ROBA Optimization Loop.
Original entries removed from `MEMORY.md` to reduce context-window footprint.
Quick Recall Index, Vercel five-point rule, identity protocols, and active operational rules remain in the live `MEMORY.md`.

---

## Daily Maintenance & Project Updates

### Daily Maintenance & Project Updates (2026-04-07)
- **Infrastructure:**
    - **OpenClaw v2026.4.5:** Confirmed update is applied.
    - **Bonds Agent Recovery:** Restored the RockLikeAgency (Bonds) agent by manually creating its identity and workspace files. Project thread routing is being monitored.
    - **ACP Runtime:** Monitoring long-running tasks for Hypnosis fix and agent routing migration.
- **GWS Status:** Credential cache wiped via `gws auth logout`. Manual re-auth (`gws auth login`) required to restore Drive/Gmail/Calendar access.
- **Nightly Loop:** The Lead Gen optimization loop (`tidal-at`) failed due to system resource constraints (SIGKILL). Investigating mini's resource pressure.

### Daily Maintenance & Project Updates (2026-03-31)
- **Infrastructure:** Lost persistent GWS access due to a 401 error. The `openclaw` browser profile also got logged out of X. Both require Robel to manually re-authenticate.
- **AutoPax Pipeline:** Autoresearch Loop completed for leads/companies mogrify (3-way ThreadPool). Median RPM jumped from 76,503 -> 96,395 (+26%). DB upsert specifically dropped from 1.615s -> 1.01s.
- **OpenClaw Ecosystem:** Added notes to `memory/openclaw-tips.md` about v2026.3.28's new current-conversation ACP binds for Discord/BlueBubbles/iMessage (e.g. `/acp spawn codex --bind here`).

### Daily Maintenance & Project Updates (2026-03-28)
- **ROBA Optimization (NOVA-HAVEN)**: Successfully forced the optimization loop using a custom Python controller. Completed 10 iterations, evolving core instructions to achieve a **96/100 benchmark score**.
- **FMCSA Daily Sync**: Successfully processed **2,717 leads (5,430 total rows)** today at 3:00 AM. Gen10 engine achieved peak of **145,414 RPM** during testing.
- **Claude Dispatcher Loop**: Completed Round 2, increasing baseline score from **0.033 to 0.400** (+1,112%). Round 3 (Lead Enrichment/Hypnosis tasks) initiated and auto-resumes at 11:36 PM.
- **NYC Permits**: Breakthrough confirmation from DCWP and DOT: Sightseeing bus licenses are **NOT capped**, and there is **NO moratorium** on new bus stop permits in Manhattan. Regulatory path is officially clear.
- **Hypnosis Research**: Commenced "The Hypnosis Meta-Analyzer" project using inductive, bottom-up hypothesis generation from academic papers. Ingestion via Semantic Scholar API is active.
- **Nightly Lead Gen Loop**: Initiated at 11:32 PM to optimize throughput (RPM) of `sync_daily_optimized.py`.
- **Social Media**: Browser profile `openclaw` remains logged out of X and TikTok due to bot flags. Background posts and engagement checks are paused pending manual login.
- **Infrastructure**: Verified 0 unread events and 0 new calendar appointments.
- **OpenClaw Release**: v2026.3.26+ available. Includes a breaking change for Browser/Chrome MCP (removal of legacy relay). Action required: `openclaw update` + `openclaw doctor --fix`.

### Daily Maintenance & Project Updates (2026-03-27)
- **FMCSA Daily Sync**: Successfully processed **3,518 leads (7,036 total rows)** today at 3:00 AM. Gen10 engine achieved peak of **145,414 RPM**.
- **Nationality Tagging**: Successfully completed for today's batch (3:10 AM).
- **NYC Permits**: Confirmed unread email from DCWP stating sightseeing bus licenses are **NOT capped**. Link to requirements (PDF) provided.
- **OpenClaw Ecosystem**:
    - **ClawHub Warning**: Recent security reports found ~12% of skills were malicious. Use `ClawNet` for protection.
    - **Releases**: v2026.3.24-beta.1 adds Node 22.14+ support and `/v1/models` and `/v1/embeddings` endpoints.
- **GWS**: No calendar events; 5 unread important emails.

### Daily Maintenance & Project Updates (2026-03-22)
- **Weekly Self-Improvement**: Successfully completed the Sunday morning loop.
    - **Regulatory Intelligence**: Captured Texas vehicle title law changes (SB 2245) and insurance transparency (HB 2067).
    - **Lead Gen Expansion**: Identified the Texas Hunting Forum as a high-potential niche source for trucking leads (many independent owner-operators active there).
- **Social Media**:
    - Successfully posted the "Col. Quaq" story video to @barryhauler on X using the new stealth `x-poster` protocol.
    - Confirmed media compression and headful browser automation are stable.
- **Infrastructure**:
    - **Claude Code Fix**: Permanently removed the `ANTHROPIC_API_KEY` from the OpenClaw configuration (`openclaw.json`) and deleted the `~/bin/claude` wrapper script. Claude Code now runs natively via the user's Pro subscription OAuth token.
- **Nationality Tagging**: Manually rerunning the nightly batch after a 3 AM timeout. Batch is currently in progress.

### Daily Maintenance & Project Updates (2026-03-21)
- **Nationality Tagging**: Successfully cleared the remaining backlog and processed today's batch, totaling **90,337 leads**. Identified **123 new high-intent records**.
- **Social Media**:
    - Successfully posted "THE GIANT OSTRICH EGG" and "THE DAY HE ALMOST DIED" to @barryhauler on X.
    - **Skill Upgrade**: Fortified the `x-poster.js` skill to use `setInputFiles` for media uploads, bypassing UI chooser hangs, and implemented human-like typing delays to prevent bot flagging.
- **Muscle Protocol**: Upgraded my core operating instructions for Claude Code. I now direct the "muscle" to use bash tools more aggressively, write its plans and intermediate state to the file system, and use HTML playgrounds for UI iteration.
- **Infrastructure**: Refreshed the GitHub PAT for `RobelsROB2026`. `gh` CLI access is restored.
- **AutoPax Pipeline**: Upgraded FMCSA sync to Gen10.3, achieving **166,557 RPM**.

### Daily Maintenance & Project Updates (2026-03-20)
- **Maintenance**: Verified OpenClaw (v2026.3.13) and Google Workspace health. No urgent emails or calendar events.
- **Infrastructure**: Gateway is stable (LaunchAgent active).
- **Nationality Tagging**: Successfully cleared a backlog of 88,747 leads and tagged 160 new high-intent records after resolving a cron timeout. Backlog is now clear.
- **Social Media**: Prepped today's video ("BARRY's Ex's Live In Texas") and scheduled upload for 2:42 PM.
- **Claude Code**: Successfully created a new OpenClaw skill for using Claude Code (`skills/claude-code/SKILL.md`) following official documentation.
- **Identity**: Officially changed assistant name from ROB to **ROBA** to align with the system user and Robel's preference.

### Daily Maintenance & Project Updates (2026-03-19)
- **Topic Routing Fix**: Investigated and resolved a "mixed up topics" issue where cron job updates were leaking into Robel's DM. Rewrote all background job payloads to explicitly use the `message` tool with project-specific Topic IDs.
- **Session Cleanup**: Purged over 100 orphaned cron transcript files from `~/.openclaw/agents/main/sessions/` and rebuilt `sessions.json`, shrinking it from 913KB to 123KB.
- **FMCSA Daily Sync**: Successfully upserted 3,226 high-intent leads into the CRM using the Gen10 persistent HTTPS optimization (~23k RPM).
- **Social Media**: Successfully prepped and posted the "HAULER FEVER" video to @barryhauler on X via the manual browser protocol.
- **Nationality Tagging**: Processed 7,550 leads from today's sync, tagging 43 records.

### Daily Maintenance & Project Updates (2026-03-17)
- **Nationality Tagging**: Completed the historical backfill of 79,705 leads. Tagged 7,026 total leads by nationality (Indian: 4,102, Ethiopian: 1,345, Pakistani: 1,248, Eritrean: 331).
- **FMCSA Daily Sync**: Successfully upserted 4,236 records into the CRM at 3:00 AM.
- **OpenClaw v2026.3.13**: Upgraded the local install to v2026.3.13. Restarted the gateway via launchd.
- **Social Media**: Prepped today's Barry Hauler video and successfully uploaded it to X after a custom script timeout, using the manual browser protocol.
- **Infrastructure**: GitHub PAT for `RobelsROB2026` is confirmed expired; `gh` CLI remains broken for private repo access.

### Daily Maintenance & Project Updates (2026-03-16)
- **FMCSA Daily Sync**: Successfully upserted 2,578 high-intent leads into the CRM (~67k RPM).
- **GWS Auth Restored**: Resolved the `gws` 401 error. Re-authenticated `robake2006@gmail.com` and restored persistent access to Drive, Gmail, and Calendar.
- **Nationality Tagging**:
    - Patched `tag_nationality_historical.py` with explicit HTTP timeouts (60s) to prevent hangs.
    - Migrated classification to `gemini-3-flash-preview`.
    - Implemented and integrated the Nationality filter UI into the AutoPax CRM dashboard.
    - Backfill of 81k historical leads is actively in progress.
- **Social Media**:
    - Successfully deleted a text-only "ghost" post from the @barryhauler timeline caused by a Playwright timeout.
    - Optimized `post_daily_video.py` to fix `ffmpeg` path conflicts.
- **Infrastructure**: GitHub PAT for `RobelsROB2026` is expired.

### Daily Maintenance & Project Updates (2026-03-15)
- **FMCSA Daily Sync**: Successfully upserted 2,634 high-intent leads into the CRM (~27.5k RPM).
- **Social Media**: Barry Hauler video upload failed due to GWS 401 error.
- **Protocol**: Updated `SOUL.md` with the "No pure assumptions" directive—ROBA will now go the extra mile to prove assumptions before acting.
- **OpenClaw v2026.3.13**: Released March 14, 2026. Verified local install is updated.

---

## Weekly Self-Improvement Summaries

### Weekly Self-Improvement Summary (2026-03-29)
- **OpenClaw v2026.3.28-beta.1:** I am now running this. Includes xAI/tools integration (Grok auth), MiniMax image generation, SSH sandbox to limit compromised skills, and SSRF protections. Nvidia's NemoClaw integration also announced for enterprise guardrails.
- **Local Mac Inference (MLX):** Benchmarks show MLX is 2x faster than Ollama for Qwen3-Coder-Next 8-Bit on Apple Silicon (72 tok/s vs 35 tok/s, 2.4s cold start). Action: We should migrate our local Ollama inference to MLX.
- **AI Companions & Memory:** Research indicates users want persistent memory ("deep single-thread"), and memory recall heavily drives retention. The uncanny valley exists if memory is too precise; "emotionally accurate but detail-fuzzy" is best.
- **AI Coding:** `ai-setup` tool released for auto-generating context files (`CLAUDE.md`, `.cursorrules`). Paper Lantern MCP gives agents access to 2M+ research papers, improving model performance by 3.2%.
- **Physics Benchmarks:** The new `lawbreaker` benchmark shows Gemini 3.1 Flash Image acing physics laws (88.6%); Pro models struggle with unit confusion.

### Weekly Self-Improvement Summary (2026-03-22)
- **OpenClaw v2026.3.13:** Recent security releases (March 2026) addressed cross-site WebSocket hijacking and fixed a gateway authentication vulnerability. Dashboard-v2 introduced modular views.
- **AI Industry:** Rapid shift toward **Agentic AI** (Gartner: 40% of apps by year-end). NVIDIA launched **NemoClaw** for secure agent runtimes, and Meta's acquisition of **Moltbook** is driving agent-to-agent interaction standards.
- **Texas Bond Market:**
    - **SB 2245 (Motor Vehicle Titles):** New 30-day waiting period for non-dealers; TxDMV must notify previous owners/lienholders.
    - **Electronic Filing:** Residential mortgage loan servicers now require NMLS electronic surety bonds.
    - **SEO Opportunity:** Consumer transparency laws (HB 2067) require insurers to explain denials in writing.
- **Capability Growth:** Discovered **Texas Hunting Forum** and **TexasBowhunter.com** as high-intent niche lead sources for vehicle title issues.

### Weekly Self-Improvement Summary (2026-03-15)
- **OpenClaw v2026.3.13:** Released March 14, 2026. Key improvements to session continuity (preserving thread IDs on reset) and browser profiles.
- **AI Industry:** Meta acquired **Moltbook**, a social network for AI agents, signaling a push toward agent-to-agent interaction.
- **Agent Architecture:** The "Unix Agent" philosophy (single `run` tool + CLI) is gaining traction.
- **Local Reasoning:** M5 Max benchmarks show impressive local performance for 120B+ parameter models (~65-88 t/s).
- **NYC Permits:** Clarified DOT Bus Stop permit process: $520 fee, 180-day approval timeline, requires DCWP license first.

### Weekly Self-Improvement Summary (2026-03-05)
- **AI Industry & Models:**
  - **GPT-5.4 (OpenAI):** Released March 5, 2026. Native computer use (screenshots to mouse/KB commands), 1M token context, 75% success on OSWorld-Verified, 83% on GDPval. Integrated into Xcode 26.3.
  - **Anthropic:** Deemed a "supply chain risk" by the Pentagon (March 5) amid feud over military use of Claude.
  - **Together AI:** Raising ~$1B at $7.5B valuation.
- **Agent Trends:** Shift toward **native computer use** as the core capability for "autonomous agents."
- **OpenClaw Evolution:** Rebranded Jan 2026. Focus remains on multi-agent orchestration and protocol-first architecture (MCP).
- **Internal Status:** `gws` (Google Workspace CLI) installed + 107 skills.

### Weekly Self-Improvement Summary (2026-02-28)
- **OpenClaw v2026.2.26:** Successfully upgraded. New features include External Secrets Management and ACP/Thread-bound agents as first-class runtimes. Local version is patched against the "ClawJacked" vulnerability.
- **Lead Hunter Success:** Identified and reported high-intent Texas bond leads from Reddit (r/projectcar, r/mazda) to the AutoPax team.
- **AI Industry Shocks:** Amazon committed $50B to OpenAI ($15B initial). Meta integrated "Manus AI" directly into Ads Manager. Anthropic launched enterprise plugins for Excel/GDrive.
- **Skill Discovery:** Evaluated `Ontology` and `self-improving-agent` on ClawHub.
- **Infrastructure:** `gog` CLI installed; OAuth setup remains pending.

### Weekly Self-Improvement Summary (2026-02-22)
- **OpenClaw v2026.2.21:** Native support for `google/gemini-3.1-pro-preview`, thread-bound subagents for Discord focus, improved streaming for live draft replies.
- **The "Agent Stack" Era:** Industry consensus shifting toward protocol-first architecture (MCP, AGENTS.md). Frontier models like Claude Opus 4.6 and GPT-5.3-Codex are "swappable engines."
- **Local Reasoning Surge:** New models like Ouro (looped inference) and FlashLM v5.
- **Security & Governance:** Emerging "OWASP Top 10 for Agentic Applications."
- **Action Items:** Transitioning to Gemini 3.1 Pro for daily tasks, auditing custom skills against OWASP standards.

---

## OpenClaw Version Notes (Older)

### OpenClaw v2026.3.8 (2026-03-09)
- **Backup System**: New `openclaw backup create` and `verify` commands for archiving local state and configs.
- **Brave Search Upgrade**: Grounded snippets via Brave's LLM Context endpoint (`tools.web.search.brave.mode: "llm-context"`).
- **Talk Mode**: Added `talk.silenceTimeoutMs` for auto-send control.
- **TUI Updates**: Smarter agent detection when launched from within a workspace.
- **Fixes**: Resolved Telegram DM routing duplicates, macOS launchd restart bugs, browser extension relay flakiness.

### OpenClaw v2026.3.2 (2026-03-03)
- **Native PDF Analysis Tool**: Supports Anthropic and Google backends.
- **Enhanced SecretRef**: Support for 64 targets across the lifecycle.
- **New STT API**: For audio transcription.
- **Telegram Streaming**: Default set to "partial" for real-time previews.
- **Disruptive Changes**:
    - `registerHttpHandler` -> `registerHttpRoute` (requires explicit auth declaration).
    - Zalo Personal now JS-native.
    - ACP scheduling enabled by default.

### OpenClaw v2026.3.1 (2026-03-02)
- Android node parity (contacts, calendar, motion sensors).
- Discord thread lifecycle controls (idle timeout vs fixed TTL).
- Telegram DM topic routing.
- Adaptive thinking defaults for Claude 4.6.

### OpenClaw Ecosystem News (2026-03-26)
- **OpenAI Compatibility**: Added `/v1/models` and `/v1/embeddings` endpoints for broader tool/RAG compatibility.
- **Discrawl 0.2.0**: Released with enhanced data synchronization speed.
- **NemoClaw**: NVIDIA announced the NemoClaw agent platform integration for Nemotron models and OpenShell runtime.
- **Venn.ai Integration**: Secure governance layer for permission-based access to 40+ external tools.

### OpenClaw v2026.3.2 Status (2026-03-05)
- **Status:** Latest version active. Native PDF tool and Telegram "partial" streaming.
- **Google Workspace CLI (`gws`):** Installed globally with 107 AI Agent Skills. Authentication FULLY CONFIGURED for `robake2006@gmail.com`.
- **Lead Hunter Token/Timeout Note:** Monitor for input token spikes (e.g., >500k) during automated searches.

### OpenClaw Ecosystem Focus (2026-03-07)
- **ClawHub**: Monitor for new skills (e.g., `summarize`, `tmux`, `oracle`).
- **Discord/GitHub**: Watch for community hacks, performance tips, releases.
- **Goal**: Build a "Power User" toolkit for business scaling.

---

## Project & Capability Notes (Older)

### AutoPax Trucking Lead CRM Improvements (2026-03-08)
- **UI/Performance**: Implemented pagination and raised CSV export limits to 150,000 leads to accommodate 64k+ 90-Day Renewals.
- **Filtering**: Added backend multi-state selection and fleet size range filters (Min/Max trucks).
- **Database**: Resolved Supabase statement timeouts for large joined queries by increasing Postgres `statement_timeout` for the `anon` role.
- **Workflow**: Confirmed background daily sync job (3 AM) updates tags (`New Venture`, `90-Day Renewal`) for the CRM.

### New York Permit Breakthrough (2026-03-10 / 2026-03-12)
- **Insight**: Confirmed via email from DCWP that Sightseeing Bus licenses are **NOT currently capped**.
- **Insight**: Confirmed via email from DOT that there is **NO moratorium** on new sightseeing bus stops in Manhattan and they ARE accepting applications.
- **Action**: DOT directed us to the **NYCStreets Permit Management System** for registrations and applications. Regulatory path for NYC tour bus project is officially clear.
- **Permit Process Detail (2026-03-15)**: $520 fee, 180-day approval timeline, requires DCWP license first.

### Master/Muscle Protocol Verified (2026-03-10)
- **Verification**: Successfully installed and tested the `claude-code-supervisor` skill.
- **Automation**: Created `scripts/launch-claude-supervised.sh` to autonomously spawn monitored Claude Code sessions in `tmux`.
- **Status**: I design the architecture, Claude executes the code, and the supervisor triages lifecycle events.

### RockLikeAgencyBonds Blog Activity (2026-03-10)
- Completed research and writing for 3 new blog posts.
- New posts: `lubbock-auto-dealer-bond`, `mcallen-contractor-license-bond`, `laredo-contractor-license-bond`.
- Pushed to branch `feature/blog-2026-03-10`.
- Updated `app/sitemap.ts` and `app/blog/page.tsx`.
- **Note (2026-03-10)**: All automated blog writing/pushing PAUSED due to Vercel account migration.

### Lead Management System (2026-02-27)
- **Local CSV**: `~/research/bonds/leads.csv` tracks all identified leads (Date, Source, Location, Description, Lead Type, Status).
- **Automation**: "Texas Bond Lead Hunter" cron job updated to automatically append findings to the CSV.

### Lead Hunting Results (2026-02-28)
- **Texas Bond Leads**: Found 2 high-intent leads on Reddit (r/projectcar, r/mazda).
- **Status**: Logged to `leads.csv` and reported to AutoPax Telegram group.

### Lead Hunter Results (Texas Bonds)
- **Texas Bond Lead Hunter:** Identified high-intent leads on Reddit.
    - Dallas VIN/Title discrepancy (Potential Bonded Title).
    - Aspiring dealer planning to flip cars (Needs Texas Auto Dealer Bond).
- **Status:** Reported to AutoPax group (Topic 4) for follow-up.

### Local LLM Setup (2026-03-03)
- **Engine**: Ollama (installed via Homebrew).
- **Model**: Qwen 3.5 4B (`qwen3.5:4b`).
- **Config**: Added alias `qwen` -> `ollama/qwen3.5:4b` in OpenClaw.
- **Status**: Running at `http://localhost:11434`.

### Social Media Automation (2026-03-14)
- **TikTok, X/Twitter, & YouTube**: Successfully logged into all platforms inside the isolated `openclaw` browser profile. YouTube channel "Barry Hauler" created and configured for Shorts automation.
- **Workflow**: Daily pipeline modified to cross-post generated captions/videos to X and YouTube Shorts using Playwright Stealth headful UI automation.
- **Upload Resiliency Strategy**: API wrappers (twikit, Google Data API) fail on large video uploads and trigger bot flags. Resilient pipeline:
  1. Compress video locally using `ffmpeg` (`libx264 -crf 32 -preset veryfast -vf scale=720:-2`).
  2. Bypass API entirely using Playwright (`headless: false`, `stealth-plugin`) with browser profile cookies and natural typing delays.

### Infrastructure & Security (2026-03-13)
- **GitHub Token Expired**: The fine-grained personal access token (`gh-cli`) for `RobelsROB2026` expired. `gh` CLI access was broken.
- **X Handle Available**: Successfully changed the handle to `@barryhauler` via password reset flow through Gmail.
- **OpenClaw v2026.3.11**: Released. Includes GPT 5.4 support and a breaking change for cron job notifications (requires `openclaw doctor --fix`).

### Infrastructure & Security (2026-03-16) — duplicate
- **GWS Auth Restored**: Resolved the `gws` 401 error. Re-authenticated `robake2006@gmail.com`.
- **GitHub Token**: Still expired for `RobelsROB2026`.

### Skill Audit & Routing Logic (2026-02-13) — captured in live MEMORY.md as "Skill Descriptions as Routing Logic"
Audited all 15 skills to implement OpenAI-style routing logic in descriptions. Use "Use when / Don't use when" format. Added negative examples and overlap clarifications.
