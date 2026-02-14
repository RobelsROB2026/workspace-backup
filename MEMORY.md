# MEMORY.md - Long-Term Memory

## Systems I've Built

### Research Library (2026-02-02)
Location: `~/research/`

Organized knowledge base by topic. Each topic gets:
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

---

## Things to Remember

- OpenClaw browser works without the Chrome extension (use profile: openclaw)
- Peekaboo needs Screen Recording permission for UI automation
- Mac mini is at home, Robel sometimes away

### Model Setup (2026-02-13 — Updated)
**Two-tier system for cost optimization:**

| Role | Model | Purpose |
|------|-------|---------|
| **Main (ROB)** | Gemini 3 Pro | Daily driving, routine tasks, conversation |
| **Ops Agent** | Claude Opus 4.6 | Create workflows, complex reasoning, system work |
| **Heartbeats** | Gemini 3 Flash | Routine checks |
| **Blog Writer** | Gemini 3 Flash | Scheduled content |
| **Lead Hunter** | Gemini 3 Flash | Daily lead search |

**Workflow:**
1. Gemini Pro handles daily tasks using existing guidelines
2. When no guideline exists or complex reasoning needed → escalate to Ops (Opus)
3. Ops creates the workflow/guideline
4. Gemini follows it going forward

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
- **Role:** Contributor (invited by Robel)
- **Current Task:** Building `/apply` page with lead capture form.
- **Blog Status:** 16 posts total. Categories: Bonded Title (6), Dealer Bonds (4), Contractor, Notary, Freight Broker, Collection Agency, Mortgage Broker, and Spanish language posts.
- **Note:** `gh` CLI authenticated as `RobelsROB2026`. PR #15 (feat: add /apply page for lead capture) successfully merged into `main` and deployed to Vercel.


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
- **Recent Update**: OpenClaw v2026.2.13 released.
  - Discord: Voice messages with waveforms.
  - Discord: Configurable presence status/activity.
  - Outbound: Write-ahead delivery queue (prevents message loss on restart).
  - Auto-reply: Implicit reply threading.
  - Telegram: Command cap (100).

- **New Tool**: Installed `gogcli` v0.10.0 via Homebrew.
  - Purpose: Full Google Workspace terminal control (Gmail, Drive, Docs, etc.).
  - Status: Awaiting OAuth2 credential setup.

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
